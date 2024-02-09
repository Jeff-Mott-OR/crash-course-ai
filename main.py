import ai
import game as gamex

import cProfile
from datetime import datetime, timedelta
import math
import matplotlib.pyplot
import os
import pstats
import pygame
import subprocess
import tempfile
from timeit import timeit

def main():
    pygame.init()
    screen = pygame.display.set_mode(gamex.SCREEN_SIZE)

    try:
        menu_choice = gamex.prompt_main_menu(screen)

        match menu_choice:
            case pygame.K_p:
                game = gamex.Game()
                clock = pygame.time.Clock()

                def render_tick():
                    frame = game.render()
                    screen.blit(frame, (0, 0))
                    pygame.display.flip()
                    clock.tick(15)

                render_tick()

                def get_keys_pressed():
                    # Using peek and poll, instead of get, because we might return before processing the whole list.
                    while pygame.event.peek():
                        event = pygame.event.poll()

                        match event.type:
                            case pygame.QUIT:
                                raise gamex.Pygame_quit_exception()

                            case pygame.KEYDOWN | pygame.KEYUP:
                                return pygame.key.get_pressed()

                    # Some key presses should fire only once, on the key down event,
                    # so if there's no key event waiting, then return all keys as not pressed.
                    return [False for ascii_key_index in range(128)]

                while game.tick(get_keys_pressed()):
                    render_tick()

            case pygame.K_t:
                class View:
                    GALLERY = 0
                    SINGLE = 1
                    SINGLE_WITH_GRAPH = 2
                    BRAIN_GRAPH = 3
                    GENERATION_SCORES = 4

                brains = [ai.Brain().mutate() for _ in range(144)]
                view = View.GALLERY
                generation_avg_stats = []
                log_next_compute_to_stream = None

                def process_pygame_events():
                    nonlocal log_next_compute_to_stream, view

                    for event in pygame.event.get():
                        match event.type:
                            case pygame.QUIT:
                                raise gamex.Pygame_quit_exception()

                            case pygame.KEYDOWN:
                                keys_pressed = pygame.key.get_pressed()
                                if keys_pressed[pygame.K_SPACE]:
                                    log_next_compute_to_stream = tempfile.NamedTemporaryFile(mode = "w", delete = False, suffix = ".txt")
                                if keys_pressed[pygame.K_TAB]:
                                    view = (view + 1) % 5 # 5 is the end enum value.

                while True:
                    games = [gamex.Game() for _ in range(len(brains))]
                    single_view_selection = None

                    def render_tick():
                        # Switching to the best performing game every frame can be jarring.
                        # Whichever game we show in single view, stay with it for a while.
                        nonlocal single_view_selection
                        if (
                            not single_view_selection
                            or (datetime.now() - single_view_selection["selected_on"]) > timedelta(seconds = 10)
                        ):
                            highest_scoring_game_index = sorted(
                                range(len(games)), key = lambda index: games[index].score, reverse = True
                            )[0]

                            def render_graph_lazy_memoize():
                                if not single_view_selection["_graph_cache"]:
                                    single_view_selection["_graph_cache"] = brains[highest_scoring_game_index].render()

                                    # We just finished rendering the brain graph. Reset the clock so we stick with it for a while.
                                    single_view_selection["selected_on"] = datetime.now()

                                return single_view_selection["_graph_cache"]

                            single_view_selection = {
                                "index": highest_scoring_game_index,
                                "game": games[highest_scoring_game_index],
                                "graph": render_graph_lazy_memoize,
                                "_graph_cache": None,
                                "selected_on": datetime.now()
                            }

                        match view:
                            case View.GALLERY:
                                num_brains_sqrt = math.ceil(len(brains) ** 0.5)

                                for game, index in zip(games, range(len(games))):
                                    frame = game.render()
                                    scaled_width, scaled_height = (frame.get_width() // num_brains_sqrt, frame.get_height() // num_brains_sqrt)
                                    scaled_frame = pygame.transform.smoothscale(frame, (scaled_width, scaled_height))
                                    screen.blit(scaled_frame, (index % num_brains_sqrt * scaled_width, index // num_brains_sqrt * scaled_height))

                                    # Rendering takes time. We need to check pygame events each iteration of this render loop
                                    # or the app won't be responsive enough.
                                    process_pygame_events()

                            case View.SINGLE | View.SINGLE_WITH_GRAPH:
                                frame = single_view_selection["game"].render()
                                screen.blit(frame, (0, 0))

                                text = pygame.font.SysFont("monospace", 18).render(
                                    f"BRAIN: {single_view_selection["index"] + 1} (Gen {len(generation_avg_stats) + 1})", False, "white"
                                )
                                screen.blit(text, (screen.get_width() - 16 - text.get_width(), 10))

                                if view == View.SINGLE_WITH_GRAPH:
                                    graph = single_view_selection["graph"]()
                                    graph_scaled = pygame.transform.smoothscale(
                                        graph, (300, 300 * graph.get_height() // graph.get_width())
                                    )
                                    screen.blit(graph_scaled, (screen.get_width() - graph_scaled.get_width() - 20, 40))

                            case View.BRAIN_GRAPH:
                                graph_scaled = pygame.transform.smoothscale(
                                    single_view_selection["graph"](), (screen.get_width(), screen.get_height())
                                )
                                screen.blit(graph_scaled, (0, 0))

                            case View.GENERATION_SCORES:
                                figure = matplotlib.pyplot.figure(figsize = (9.6, 5.4), layout = "constrained")

                                # Flip between two graphs, and stay on each one for about 10 seconds.
                                if datetime.now().second // 10 % 2 == 0:
                                    matplotlib.pyplot.plot([avg_stat["score"] for avg_stat in generation_avg_stats])
                                    matplotlib.pyplot.ylabel("AVG GAME SCORE")
                                else:
                                    matplotlib.pyplot.plot([avg_stat["mutation_rate"] for avg_stat in generation_avg_stats])
                                    matplotlib.pyplot.ylabel("AVG BRAIN MUTATION")

                                matplotlib.pyplot.xlabel("GENERATION")
                                figure_canvas = matplotlib.backends.backend_agg.FigureCanvas(figure)
                                figure_canvas.draw()
                                matplotlib.pyplot.close(figure)

                                surface = pygame.image.frombuffer(
                                    figure_canvas.get_renderer().buffer_rgba(),
                                    (int(figure_canvas.get_renderer().width), int(figure_canvas.get_renderer().height)),
                                    "RGBA"
                                )
                                surface_scaled = pygame.transform.smoothscale(surface, (screen.get_width(), screen.get_height()))
                                screen.blit(surface_scaled, (0, 0))

                        pygame.display.flip()

                    render_tick()
                    last_render_time = datetime.now()

                    def get_keys_pressed(game, brain):
                        nonlocal log_next_compute_to_stream

                        next_move_keys = brain.compute_next_move(game, log_next_compute_to_stream)

                        if log_next_compute_to_stream:
                            # `startfile` for Windows, `open` for all else.
                            if hasattr(os, "startfile"):
                                os.startfile(log_next_compute_to_stream.name)
                            else:
                                subprocess.run(["open", log_next_compute_to_stream.name])
                            log_next_compute_to_stream = False

                        return [
                            next_move_keys[ascii_key_index] if ascii_key_index in next_move_keys else False
                                for ascii_key_index in range(128)
                        ]

                    while any(list(map(
                        lambda game_brain: game_brain[0].tick(get_keys_pressed(game_brain[0], game_brain[1])),
                        zip(games, brains)
                    ))):
                        # Rendering is a performance bottleneck. The less we render, the faster we compute.
                        if (datetime.now() - last_render_time) >= timedelta(milliseconds = 250):
                            render_tick()
                            last_render_time = datetime.now()

                        process_pygame_events()

                    generation_avg_stats.append({
                        "score": sum(map(lambda game: game.score, games)) / len(games),
                        "mutation_rate": sum(map(lambda brain: brain._probability_of_mutation, brains)) / len(brains)
                    })

                    brains_scores = [(brain, game.score) for game, brain in zip(games, brains)]
                    brains_scores_sorted = sorted(brains_scores, key = lambda brain_score: brain_score[1], reverse = True)
                    fittest_cutoff = len(brains_scores_sorted) // 2
                    brains = [
                        brains_scores_sorted[index % fittest_cutoff][0].mutate()
                            for index in range(len(brains))
                    ]

    except gamex.Pygame_quit_exception:
        pass

# Normal run.
main()

# Profile run.
# cProfile.run("main()", sort = pstats.SortKey.CUMULATIVE)
