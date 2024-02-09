# Oregon Trail hunting mini-game with neural network AI

Inspired from [CrashCourse AI](https://www.youtube.com/playlist?list=PL8dPuuaLjXtO65LeD2p4_Sb5XQ51par_b), I used Python and Pygame to re-create the hunting mini-game from the 1970's Oregon Trail. Then I made a neural network AI that learns to play the game on its own and gets better over successive generations.

## Dependencies

You'll need [Python 3](https://www.python.org/downloads/). And you'll need the following Python packages.

    python3 -m pip install pygame matplotlib networkx

Then you can run the game script.

    $ python3 main.py

## Screenshots

On the main menu screen, you'll get the option to either play the game or train the AI. If you pless "P" to play the game, then you'll get one minute to hunt and shoot as many buffalo as you can. Press "ENTER" to start and stop moving your character. Press "WSAD" to point your character up, down, left, and right. And press "SPACE" to shoot.

![](/../assets/demo_main_menu.png)

![](/../assets/demo_play.png)

Or if you press "T" to train the AI, then you'll see a gallery of 144 games being played simultaneously. Each of those games is controlled by a neural network AI "brain". Each brain will be mutated in its own random way. By sheer dumb luck, some of those mutations will be beneficial, and some won't. The brains that get the highest game score are used to populate the next generation of AI brains, each with additional small and random mutations. Rinse repeat 'til you run out of cake and the science gets done.

![](/../assets/demo_ai_gallery.png)

From the gallery of games, press "TAB" to zoom in to a single game's view.

![](/../assets/demo_ai_single_view.png)

Press "TAB" again to show a visualization of neurons and weighted connections from the neural network AI brain that's controlling the current game. Press "TAB" again to zoom that brain visualization to full screen. It doesn't tell you anything useful, but it's interesting to look at.

![](/../assets/demo_ai_single_view_with_brain_graph.png)

![](/../assets/demo_ai_brain_graph.png)

On any of the AI screens, press "SPACE" to view a dump of a brain's connection weights and computed neuron values.

![](/../assets/demo_brain_dump.png)

Press "TAB" again to view the graphed average game score of each generation of AI brains. This view is useful to measure and compare how well an AI performs as we tweak its settings.

![](/../assets/demo_ai_score_progression.png)
