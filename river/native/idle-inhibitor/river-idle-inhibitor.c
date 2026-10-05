#define _GNU_SOURCE

#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <wayland-client.h>

#include "idle-inhibit-unstable-v1-client-protocol.h"
#include "wlr-layer-shell-unstable-v1-client-protocol.h"

static struct wl_display *display;
static struct wl_compositor *compositor;
static struct wl_shm *shm;
static struct zwlr_layer_shell_v1 *layer_shell;
static struct zwp_idle_inhibit_manager_v1 *idle_manager;
static struct wl_surface *surface;
static struct zwlr_layer_surface_v1 *layer_surface;
static struct wl_buffer *buffer;
static struct zwp_idle_inhibitor_v1 *inhibitor;
static volatile sig_atomic_t running = 1;
static int mapped;

static uint32_t
minimum(uint32_t first, uint32_t second)
{
    return first < second ? first : second;
}

static void
handle_signal(int signal_number)
{
    (void)signal_number;
    running = 0;
}

static struct wl_buffer *
make_transparent_buffer(void)
{
    int fd = memfd_create("river-idle-inhibitor", MFD_CLOEXEC);
    if (fd < 0 || ftruncate(fd, 4) < 0) {
        perror("creating shared-memory buffer");
        if (fd >= 0)
            close(fd);
        return NULL;
    }

    uint32_t *pixel = mmap(NULL, 4, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (pixel == MAP_FAILED) {
        perror("mapping shared-memory buffer");
        close(fd);
        return NULL;
    }
    *pixel = 0;

    struct wl_shm_pool *pool = wl_shm_create_pool(shm, fd, 4);
    struct wl_buffer *result = wl_shm_pool_create_buffer(
        pool, 0, 1, 1, 4, WL_SHM_FORMAT_ARGB8888);
    wl_shm_pool_destroy(pool);
    munmap(pixel, 4);
    close(fd);
    return result;
}

static void
layer_configure(void *data, struct zwlr_layer_surface_v1 *configured_surface,
    uint32_t serial, uint32_t width, uint32_t height)
{
    (void)data;
    (void)width;
    (void)height;
    zwlr_layer_surface_v1_ack_configure(configured_surface, serial);

    if (mapped)
        return;

    buffer = make_transparent_buffer();
    if (!buffer) {
        running = 0;
        return;
    }

    inhibitor = zwp_idle_inhibit_manager_v1_create_inhibitor(
        idle_manager, surface);
    wl_surface_attach(surface, buffer, 0, 0);
    wl_surface_damage(surface, 0, 0, 1, 1);
    wl_surface_commit(surface);
    mapped = 1;
}

static void
layer_closed(void *data, struct zwlr_layer_surface_v1 *closed_surface)
{
    (void)data;
    (void)closed_surface;
    running = 0;
}

static const struct zwlr_layer_surface_v1_listener layer_listener = {
    .configure = layer_configure,
    .closed = layer_closed,
};

static void
registry_global(void *data, struct wl_registry *registry, uint32_t name,
    const char *interface, uint32_t version)
{
    (void)data;
    if (strcmp(interface, wl_compositor_interface.name) == 0) {
        compositor = wl_registry_bind(
            registry, name, &wl_compositor_interface, minimum(version, 4));
    } else if (strcmp(interface, wl_shm_interface.name) == 0) {
        shm = wl_registry_bind(registry, name, &wl_shm_interface, 1);
    } else if (strcmp(interface, zwlr_layer_shell_v1_interface.name) == 0) {
        layer_shell = wl_registry_bind(registry, name,
            &zwlr_layer_shell_v1_interface, minimum(version, 4));
    } else if (strcmp(
                   interface, zwp_idle_inhibit_manager_v1_interface.name) == 0) {
        idle_manager = wl_registry_bind(registry, name,
            &zwp_idle_inhibit_manager_v1_interface, 1);
    }
}

static void
registry_remove(void *data, struct wl_registry *registry, uint32_t name)
{
    (void)data;
    (void)registry;
    (void)name;
}

static const struct wl_registry_listener registry_listener = {
    .global = registry_global,
    .global_remove = registry_remove,
};

int
main(void)
{
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    display = wl_display_connect(NULL);
    if (!display) {
        fprintf(stderr, "river-idle-inhibitor: cannot connect to Wayland\n");
        return 1;
    }

    struct wl_registry *registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &registry_listener, NULL);
    wl_display_roundtrip(display);

    if (!compositor || !shm || !layer_shell || !idle_manager) {
        fprintf(stderr,
            "river-idle-inhibitor: compositor lacks a required protocol\n");
        return 1;
    }

    surface = wl_compositor_create_surface(compositor);
    struct wl_region *empty_region = wl_compositor_create_region(compositor);
    wl_surface_set_input_region(surface, empty_region);
    wl_region_destroy(empty_region);

    layer_surface = zwlr_layer_shell_v1_get_layer_surface(layer_shell, surface,
        NULL, ZWLR_LAYER_SHELL_V1_LAYER_OVERLAY, "river-idle-inhibitor");
    zwlr_layer_surface_v1_add_listener(layer_surface, &layer_listener, NULL);
    zwlr_layer_surface_v1_set_size(layer_surface, 1, 1);
    zwlr_layer_surface_v1_set_anchor(layer_surface,
        ZWLR_LAYER_SURFACE_V1_ANCHOR_BOTTOM |
            ZWLR_LAYER_SURFACE_V1_ANCHOR_LEFT);
    zwlr_layer_surface_v1_set_exclusive_zone(layer_surface, 0);
    zwlr_layer_surface_v1_set_keyboard_interactivity(
        layer_surface, ZWLR_LAYER_SURFACE_V1_KEYBOARD_INTERACTIVITY_NONE);
    wl_surface_commit(surface);

    while (running) {
        if (wl_display_dispatch(display) < 0) {
            if (errno == EINTR)
                continue;
            break;
        }
    }

    if (inhibitor)
        zwp_idle_inhibitor_v1_destroy(inhibitor);
    if (buffer)
        wl_buffer_destroy(buffer);
    if (layer_surface)
        zwlr_layer_surface_v1_destroy(layer_surface);
    if (surface)
        wl_surface_destroy(surface);
    zwp_idle_inhibit_manager_v1_destroy(idle_manager);
    zwlr_layer_shell_v1_destroy(layer_shell);
    wl_shm_destroy(shm);
    wl_compositor_destroy(compositor);
    wl_registry_destroy(registry);
    wl_display_disconnect(display);
    return 0;
}
