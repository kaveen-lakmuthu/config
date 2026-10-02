#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <wayland-client.h>

#include "river-status-unstable-v1-client-protocol.h"

struct output_state {
    struct wl_output *output;
    struct zriver_output_status_v1 *status;
    uint32_t focused_tags;
    bool have_tags;
    struct output_state *next;
};

struct app_state {
    struct wl_display *display;
    struct zriver_status_manager_v1 *status_manager;
    struct zriver_seat_status_v1 *seat_status;
    struct wl_seat *seat;
    struct wl_output *focused_output;
    struct output_state *outputs;
};

static void output_focused_tags(void *data,
                                struct zriver_output_status_v1 *status,
                                uint32_t tags) {
    (void)status;
    struct output_state *output = data;
    output->focused_tags = tags;
    output->have_tags = true;
}

static void output_view_tags(void *data,
                             struct zriver_output_status_v1 *status,
                             struct wl_array *tags) {
    (void)data;
    (void)status;
    (void)tags;
}

static void output_urgent_tags(void *data,
                               struct zriver_output_status_v1 *status,
                               uint32_t tags) {
    (void)data;
    (void)status;
    (void)tags;
}

static void output_layout_name(void *data,
                               struct zriver_output_status_v1 *status,
                               const char *name) {
    (void)data;
    (void)status;
    (void)name;
}

static void output_layout_name_clear(void *data,
                                     struct zriver_output_status_v1 *status) {
    (void)data;
    (void)status;
}

static const struct zriver_output_status_v1_listener output_listener = {
    .focused_tags = output_focused_tags,
    .view_tags = output_view_tags,
    .urgent_tags = output_urgent_tags,
    .layout_name = output_layout_name,
    .layout_name_clear = output_layout_name_clear,
};

static void seat_focused_output(void *data,
                                struct zriver_seat_status_v1 *status,
                                struct wl_output *output) {
    (void)status;
    struct app_state *app = data;
    app->focused_output = output;
}

static void seat_unfocused_output(void *data,
                                  struct zriver_seat_status_v1 *status,
                                  struct wl_output *output) {
    (void)status;
    struct app_state *app = data;
    if (app->focused_output == output) {
        app->focused_output = NULL;
    }
}

static void seat_focused_view(void *data,
                              struct zriver_seat_status_v1 *status,
                              const char *title) {
    (void)data;
    (void)status;
    (void)title;
}

static void seat_mode(void *data,
                      struct zriver_seat_status_v1 *status,
                      const char *name) {
    (void)data;
    (void)status;
    (void)name;
}

static const struct zriver_seat_status_v1_listener seat_listener = {
    .focused_output = seat_focused_output,
    .unfocused_output = seat_unfocused_output,
    .focused_view = seat_focused_view,
    .mode = seat_mode,
};

static void registry_global(void *data,
                            struct wl_registry *registry,
                            uint32_t name,
                            const char *interface,
                            uint32_t version) {
    struct app_state *app = data;

    if (strcmp(interface, zriver_status_manager_v1_interface.name) == 0) {
        const uint32_t bind_version = version < 4 ? version : 4;
        app->status_manager = wl_registry_bind(
            registry, name, &zriver_status_manager_v1_interface, bind_version);
        return;
    }

    if (strcmp(interface, wl_seat_interface.name) == 0 && app->seat == NULL) {
        app->seat = wl_registry_bind(registry, name, &wl_seat_interface, 1);
        return;
    }

    if (strcmp(interface, wl_output_interface.name) == 0) {
        struct output_state *output = calloc(1, sizeof(*output));
        if (output == NULL) {
            fprintf(stderr, "river-cycle-tags: out of memory\n");
            exit(EXIT_FAILURE);
        }

        output->output = wl_registry_bind(registry, name, &wl_output_interface, 1);
        output->next = app->outputs;
        app->outputs = output;
    }
}

static void registry_global_remove(void *data,
                                   struct wl_registry *registry,
                                   uint32_t name) {
    (void)data;
    (void)registry;
    (void)name;
}

static const struct wl_registry_listener registry_listener = {
    .global = registry_global,
    .global_remove = registry_global_remove,
};

static struct output_state *focused_output_state(struct app_state *app) {
    for (struct output_state *output = app->outputs; output != NULL; output = output->next) {
        if (output->output == app->focused_output) {
            return output;
        }
    }
    return NULL;
}

static unsigned int first_set_bit(uint32_t tags) {
    unsigned int index = 0;
    while ((tags & 1u) == 0u) {
        tags >>= 1u;
        index++;
    }
    return index;
}

static unsigned int last_set_bit(uint32_t tags) {
    unsigned int index = 0;
    while ((tags >>= 1u) != 0u) {
        index++;
    }
    return index;
}

static uint32_t next_tag(uint32_t focused_tags, unsigned int count, bool forward) {
    const uint32_t visible_mask = count == 32 ? UINT32_MAX : ((1u << count) - 1u);
    const uint32_t visible_tags = focused_tags & visible_mask;

    if (visible_tags == 0u || visible_tags == visible_mask) {
        return forward ? 1u : (1u << (count - 1u));
    }

    unsigned int current;
    if ((visible_tags & (visible_tags - 1u)) == 0u) {
        current = first_set_bit(visible_tags);
    } else {
        current = forward ? last_set_bit(visible_tags) : first_set_bit(visible_tags);
    }

    const unsigned int target = forward
        ? (current + 1u) % count
        : (current == 0u ? count - 1u : current - 1u);
    return 1u << target;
}

static void usage(FILE *stream) {
    fprintf(stream, "usage: river-cycle-tags next|previous [tag-count]\n");
}

int main(int argc, char **argv) {
    if (argc < 2 || argc > 3 ||
        (strcmp(argv[1], "next") != 0 && strcmp(argv[1], "previous") != 0)) {
        usage(stderr);
        return EXIT_FAILURE;
    }

    unsigned long requested_count = 9;
    if (argc == 3) {
        char *end = NULL;
        errno = 0;
        requested_count = strtoul(argv[2], &end, 10);
        if (errno != 0 || end == argv[2] || *end != '\0' ||
            requested_count < 1 || requested_count > 32) {
            fprintf(stderr, "river-cycle-tags: tag-count must be between 1 and 32\n");
            return EXIT_FAILURE;
        }
    }

    struct app_state app = {0};
    app.display = wl_display_connect(NULL);
    if (app.display == NULL) {
        fprintf(stderr, "river-cycle-tags: unable to connect to the Wayland display\n");
        return EXIT_FAILURE;
    }

    struct wl_registry *registry = wl_display_get_registry(app.display);
    wl_registry_add_listener(registry, &registry_listener, &app);

    if (wl_display_roundtrip(app.display) < 0) {
        fprintf(stderr, "river-cycle-tags: failed to read the Wayland registry\n");
        return EXIT_FAILURE;
    }

    if (app.status_manager == NULL || app.seat == NULL || app.outputs == NULL) {
        fprintf(stderr, "river-cycle-tags: River status, seat, or output is unavailable\n");
        return EXIT_FAILURE;
    }

    for (struct output_state *output = app.outputs; output != NULL; output = output->next) {
        output->status = zriver_status_manager_v1_get_river_output_status(
            app.status_manager, output->output);
        zriver_output_status_v1_add_listener(output->status, &output_listener, output);
    }

    app.seat_status = zriver_status_manager_v1_get_river_seat_status(
        app.status_manager, app.seat);
    zriver_seat_status_v1_add_listener(app.seat_status, &seat_listener, &app);

    if (wl_display_roundtrip(app.display) < 0) {
        fprintf(stderr, "river-cycle-tags: failed to receive River status\n");
        return EXIT_FAILURE;
    }

    struct output_state *output = focused_output_state(&app);
    if (output == NULL || !output->have_tags) {
        fprintf(stderr, "river-cycle-tags: no focused output/tag state available\n");
        return EXIT_FAILURE;
    }

    const bool forward = strcmp(argv[1], "next") == 0;
    const uint32_t tag = next_tag(output->focused_tags, (unsigned int)requested_count, forward);

    char tag_text[16];
    snprintf(tag_text, sizeof(tag_text), "%u", tag);

    char *const riverctl_argv[] = {
        "riverctl",
        "set-focused-tags",
        tag_text,
        NULL,
    };
    execvp(riverctl_argv[0], riverctl_argv);

    fprintf(stderr, "river-cycle-tags: unable to execute riverctl: %s\n", strerror(errno));
    return EXIT_FAILURE;
}

