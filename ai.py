import copy
import game as gamex
import matplotlib.pyplot
import networkx
import numpy
import pygame
import random

NUM_INPUTS_PER_BUFFALO = 3 # X, Y, direction.
NUM_BUFFALO_TO_TRACK = 5
NUM_INPUTS_PER_OBSTACLE = 4 # X, Y, W, H
NUM_OBSTACLES_TO_TRACK = 3
NUM_INPUTS = NUM_INPUTS_PER_BUFFALO * NUM_BUFFALO_TO_TRACK + NUM_INPUTS_PER_OBSTACLE * NUM_OBSTACLES_TO_TRACK
NUM_OUTPUTS = 6 # WSAD + ENTER + SPACE.
NUM_HIDDEN_LAYERS = 1
NUM_NEURONS_PER_LAYER = round((NUM_INPUTS + NUM_OUTPUTS) * 2 / 3)

class Brain:
    def __init__(self):
        # WARNING! Magic number! This 0.125 is a random guess. But this brain's
        # probability of mutation itself can mutate. Over generations,
        # this value may grow or shrink and eventually converge on an optimal number.
        self._probability_of_mutation = 0.125

        self._input_values = numpy.zeros(NUM_INPUTS)

        self._input_layer_edge_weights = numpy.zeros((NUM_INPUTS, NUM_NEURONS_PER_LAYER))
        self._input_biases = numpy.zeros(NUM_NEURONS_PER_LAYER)

        self._hidden_layer_edge_weights = numpy.zeros((NUM_NEURONS_PER_LAYER, NUM_NEURONS_PER_LAYER, NUM_HIDDEN_LAYERS))
        self._hidden_biases = numpy.zeros((NUM_NEURONS_PER_LAYER, NUM_HIDDEN_LAYERS))

        self._output_layer_edge_weights = numpy.zeros((NUM_NEURONS_PER_LAYER, NUM_OUTPUTS))
        self._output_biases = numpy.zeros(NUM_OUTPUTS)

        self._output_values = numpy.zeros(NUM_OUTPUTS)

    def mutate(self):
        # Mutate and return a *copy*. The self object remains unchanged.
        self_copy = copy.deepcopy(self)

        if random.random() < self_copy._probability_of_mutation:
            self_copy._probability_of_mutation = max(0.001, min(1,
                self_copy._probability_of_mutation + random.gauss(0.0, 0.025)
            ))

        for input_index in range(NUM_INPUTS):
            for neuron_index in range(NUM_NEURONS_PER_LAYER):
                if random.random() < self_copy._probability_of_mutation:
                    self_copy._input_layer_edge_weights[input_index, neuron_index] += random.gauss()

        for neuron_index in range(NUM_NEURONS_PER_LAYER):
            if random.random() < self_copy._probability_of_mutation:
                self_copy._input_biases[neuron_index] += random.gauss()

        for neuron_index_lhs in range(NUM_NEURONS_PER_LAYER):
            for neuron_index_rhs in range(NUM_NEURONS_PER_LAYER):
                for hidden_layer_index in range(NUM_HIDDEN_LAYERS):
                    if random.random() < self_copy._probability_of_mutation:
                        self_copy._hidden_layer_edge_weights[neuron_index_lhs, neuron_index_rhs, hidden_layer_index] += random.gauss()

        for neuron_index in range(NUM_NEURONS_PER_LAYER):
            for hidden_layer_index in range(NUM_HIDDEN_LAYERS):
                if random.random() < self_copy._probability_of_mutation:
                    self_copy._hidden_biases[neuron_index, hidden_layer_index] += random.gauss()

        for neuron_index in range(NUM_NEURONS_PER_LAYER):
            for output_index in range(NUM_OUTPUTS):
                if random.random() < self_copy._probability_of_mutation:
                    self_copy._output_layer_edge_weights[neuron_index, output_index] += random.gauss()

        for output_index in range(NUM_OUTPUTS):
            if random.random() < self_copy._probability_of_mutation:
                self_copy._output_biases[output_index] += random.gauss()

        return self_copy

    def compute_next_move(self, game_state, logger = None):
        living_buffalos_distances = [
            (
                buffalo,
                (
                    (buffalo.rect.centerx - game_state.hunter.rect.centerx) ** 2
                    + (buffalo.rect.centery - game_state.hunter.rect.centery) ** 2
                ) ** 0.5
            )
                for buffalo in filter(lambda buffalo: buffalo.alive, game_state.buffalos)
        ]
        living_buffalos_distances_sorted = sorted(living_buffalos_distances, key = lambda buffalo_distance: buffalo_distance[1])

        all_obstacles = (
            game_state.obstacles
            + gamex.INVISIBLE_WALLS
            + [buffalo.rect for buffalo in game_state.buffalos if not buffalo.alive]
        )
        obstacles_distances = [
            (
                obstacle,
                (
                    (obstacle.centerx - game_state.hunter.rect.centerx) ** 2
                    + (obstacle.centery - game_state.hunter.rect.centery) ** 2
                ) ** 0.5
            )
                for obstacle in all_obstacles
        ]
        obstacles_distances_sorted = sorted(obstacles_distances, key = lambda obstacle_distance: obstacle_distance[1])

        for input_index in range(NUM_INPUTS):
            self._input_values[input_index] = 0

        for buffalo_index in range(min(NUM_BUFFALO_TO_TRACK, len(living_buffalos_distances_sorted))):
            buffalo_distance = living_buffalos_distances_sorted[buffalo_index]
            buffalo = buffalo_distance[0]
            segment_begin = NUM_INPUTS_PER_BUFFALO * buffalo_index

            self._input_values[segment_begin + 0] = buffalo.rect.centerx - game_state.hunter.rect.centerx
            self._input_values[segment_begin + 1] = buffalo.rect.centery - game_state.hunter.rect.centery
            self._input_values[segment_begin + 2] = buffalo.direction
        for obstacle_index in range(min(NUM_OBSTACLES_TO_TRACK, len(obstacles_distances_sorted))):
            obstacle_distance = obstacles_distances_sorted[obstacle_index]
            obstacle = obstacle_distance[0]
            segment_begin = NUM_INPUTS_PER_BUFFALO * NUM_BUFFALO_TO_TRACK + NUM_OBSTACLES_TO_TRACK * obstacle_index

            self._input_values[segment_begin + 0] = obstacle.centerx - game_state.hunter.rect.centerx
            self._input_values[segment_begin + 1] = obstacle.centery - game_state.hunter.rect.centery
            self._input_values[segment_begin + 2] = obstacle.width
            self._input_values[segment_begin + 3] = obstacle.height

        layer_neuron_values = list(map(
            lambda value: max(0, value),
            numpy.dot(self._input_values, self._input_layer_edge_weights) + self._input_biases
        ))

        if logger:
            logger.write("PROBABILITY OF MUTATION:\n" + str(self._probability_of_mutation) + "\n\n")
            logger.write("INPUT VALUES:\n" + str(self._input_values) + "\n\n")
            logger.write("INPUT LAYER EDGE WEIGHTS:\n" + str(self._input_layer_edge_weights) + "\n\n")
            logger.write("INPUT LAYER BIASES:\n" + str(self._input_biases) + "\n\n")
            logger.write("INPUT LAYER COMPUTED NODE VALUES:\n" + str(layer_neuron_values) + "\n\n")

        for hidden_layer_index in range(NUM_HIDDEN_LAYERS):
            layer_neuron_values = list(map(
                lambda value: max(0, value),
                numpy.array([
                    numpy.dot(layer_neuron_values, self._hidden_layer_edge_weights[neuron_index, :, hidden_layer_index])
                        for neuron_index in range(NUM_NEURONS_PER_LAYER)
                ]) + self._hidden_biases[:, hidden_layer_index]
            ))

            if logger:
                logger.write("HIDDEN LAYER EDGE WEIGHTS:\n" + str(self._hidden_layer_edge_weights[:, :, hidden_layer_index]) + "\n\n")
                logger.write("HIDDEN LAYER BIASES:\n" + str(self._hidden_biases[:, hidden_layer_index]) + "\n\n")
                logger.write("HIDDEN LAYER COMPUTED NODE VALUES:\n" + str(layer_neuron_values) + "\n\n")

        self._output_values = numpy.dot(layer_neuron_values, self._output_layer_edge_weights) + self._output_biases

        if logger:
            logger.write("OUTPUT LAYER EDGE WEIGHTS:\n" + str(self._output_layer_edge_weights) + "\n\n")
            logger.write("OUTPUT LAYER BIASES:\n" + str(self._output_biases) + "\n\n")
            logger.write("OUTPUT VALUES:\n" + str(self._output_values) + "\n\n")

        return dict([
            (pygame.K_w, self._output_values[0] > 0),
            (pygame.K_s, self._output_values[1] > 0),
            (pygame.K_a, self._output_values[2] > 0),
            (pygame.K_d, self._output_values[3] > 0),
            (pygame.K_RETURN, self._output_values[4] > 0),
            (pygame.K_SPACE, self._output_values[5] > 0),
        ])

    def render(self):
        graph = networkx.DiGraph()

        # Inputs.
        node_column = 0
        for input_index in range(NUM_INPUTS):
            node_id = f"x_{node_column}_y_{input_index}"
            graph.add_node(node_id, pos = (node_column, input_index))

        # Input layer.
        node_column += 1
        for neuron_index in range(NUM_NEURONS_PER_LAYER):
            node_id = f"x_{node_column}_y_{neuron_index}"
            graph.add_node(node_id, pos = (node_column, neuron_index / NUM_NEURONS_PER_LAYER * NUM_INPUTS))
        for input_index in range(NUM_INPUTS):
            node_id_lhs = f"x_{node_column - 1}_y_{input_index}"
            for neuron_index in range(NUM_NEURONS_PER_LAYER):
                node_id_rhs = f"x_{node_column}_y_{neuron_index}"
                graph.add_edge(node_id_lhs, node_id_rhs, weight = self._input_layer_edge_weights[input_index][neuron_index])

        # Hidden layers.
        for hidden_layer_index in range(NUM_HIDDEN_LAYERS):
            node_column += 1
            for neuron_index in range(NUM_NEURONS_PER_LAYER):
                node_id = f"x_{node_column}_y_{neuron_index}"
                graph.add_node(node_id, pos = (node_column, neuron_index / NUM_NEURONS_PER_LAYER * NUM_INPUTS))
            for neuron_index_lhs in range(NUM_NEURONS_PER_LAYER):
                node_id_lhs = f"x_{node_column - 1}_y_{neuron_index_lhs}"
                for neuron_index_rhs in range(NUM_NEURONS_PER_LAYER):
                    node_id_rhs = f"x_{node_column}_y_{neuron_index_rhs}"
                    graph.add_edge(
                        node_id_lhs,
                        node_id_rhs,
                        weight = self._hidden_layer_edge_weights[neuron_index_lhs][neuron_index_rhs][hidden_layer_index]
                    )

        # Output layer.
        node_column += 1
        for output_index in range(NUM_OUTPUTS):
            node_id = f"x_{node_column}_y_{output_index}"
            graph.add_node(node_id, pos = (node_column, output_index / NUM_OUTPUTS * NUM_INPUTS))
        for neuron_index in range(NUM_NEURONS_PER_LAYER):
            node_id_lhs = f"x_{node_column - 1}_y_{neuron_index}"
            for output_index in range(NUM_OUTPUTS):
                node_id_rhs = f"x_{node_column}_y_{output_index}"
                graph.add_edge(node_id_lhs, node_id_rhs, weight = self._output_layer_edge_weights[neuron_index][output_index])

        figure = matplotlib.pyplot.figure(figsize = (9.6, 5.4), layout = "constrained")
        figure_axes = figure.gca()
        networkx.draw_networkx_nodes(
            graph,
            networkx.get_node_attributes(graph, "pos"),
            ax = figure_axes,
            node_size = 200,
            node_color = "blue",
            alpha = 0.35,
        )
        edges_weights_to_render = [
            (edge, weight)
                for edge, weight in networkx.get_edge_attributes(graph, "weight").items()
                if weight != 0
        ]
        networkx.draw_networkx_edges(
            graph,
            networkx.get_node_attributes(graph, "pos"),
            ax = figure_axes,
            edgelist = list(map(lambda edge_weight: edge_weight[0], edges_weights_to_render)),
            edge_color = list(map(lambda edge_weight: edge_weight[1], edges_weights_to_render)),
            edge_cmap = matplotlib.pyplot.cm.Blues,
        )
        figure_canvas = matplotlib.backends.backend_agg.FigureCanvas(figure)
        figure_canvas.draw()
        matplotlib.pyplot.close(figure)

        surface = pygame.image.frombuffer(
            figure_canvas.get_renderer().buffer_rgba(),
            (int(figure_canvas.get_renderer().width), int(figure_canvas.get_renderer().height)),
            "RGBA"
        )

        return surface
