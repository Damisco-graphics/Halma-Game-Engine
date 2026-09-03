# Halma Game Engine

A two-player graphical **Halma game engine** built in Python with Tkinter. The system manages the complete gameplay loop for human players, including board initialization, legal move generation, multi-jump mechanics, rule enforcement, turn management, scoring, move timing, and win detection.

The project focuses on building a reliable game-state and interaction system with clear graphical feedback for players.

## Features

* **Two-player human gameplay**
* Interactive graphical board built with **Tkinter Canvas**
* Supports multiple board sizes:

  * 8 × 8
  * 10 × 10
  * 16 × 16
* Configurable move time limit
* Interactive piece selection
* Automatic highlighting of legal moves
* Single-step movement
* Single and multi-jump moves
* Jumping over both friendly and opposing pieces
* Blocking-rule enforcement
* No-return rule for jump sequences
* Turn management
* Move counting
* Real-time player scoring
* Countdown move timer
* Win-condition detection
* End-of-game notification
* Recent-move highlighting
* Error and rule-violation feedback

## Game Mechanics

### Movement

A piece can move to an adjacent empty square horizontally, vertically, or diagonally.

Pieces can also jump over an adjacent piece onto an empty square immediately beyond it. Multiple jumps can be chained together within a single turn.

Jump sequences can be ended voluntarily, while preventing a jump from returning to the square where the sequence began.

### Camp and Blocking Rules

The implementation enforces Halma movement restrictions within the players' camps.

Once a piece enters the opponent's camp, it cannot leave that camp.

Pieces remaining in their home camp must make moves that advance them toward the opponent's camp, preventing players from stalling by moving backward or sideways within their starting area.

## Board and Game State

The game maintains the current state of the board and graphical objects through structured data associated with each position.

Key state information includes:

* Piece locations
* Available legal moves
* Current player
* Move history/highlighting
* Player scores
* Distance-to-goal calculations
* Move timing

The board supports different dimensions while maintaining the same underlying movement and game-state logic.

## Architecture

The game is organized around two primary classes:

### `Position`

Responsible for piece-level behavior and movement operations.

Key functionality includes:

* Creating and updating graphical pieces
* Calculating distance to the goal
* Handling mouse interactions
* Generating adjacent positions
* Executing standard moves
* Executing jump moves
* Managing graphical shapes

### `Board`

Responsible for board-level and game-level state.

Key functionality includes:

* Managing player turns
* Highlighting the active turn
* Managing available moves
* Maintaining board state
* Tracking player scores
* Updating graphical state

## Scoring

Player scores are updated throughout the game based on the position of each piece relative to the opponent's goal camp.

Pieces completely inside the opponent's camp receive full credit, while pieces outside the camp contribute based on their distance from the goal.

This provides a continuous measure of progress toward the win condition rather than relying exclusively on the final game state.

## Win Condition

A player wins when all squares in the opponent's camp are occupied by that player's pieces.

When a win occurs, the game ends and displays the final game information, including:

* Winning player
* Number of move cycles
* Final score for each player

## User Interface

The graphical interface provides continuous feedback during gameplay.

The interface includes:

* Graphical game board
* Player pieces
* Selected-piece highlighting
* Legal-move highlighting
* Recent-move indicators
* Current-player indicator
* Move timer
* Move count
* Player scores
* Error and rule-violation messages
* Game-end notification

Tkinter Canvas primitives such as `create_oval`, `create_rectangle`, and `delete` are used to manage the board and graphical elements.

## Example Gameplay Flow

```text
1. Initialize the board
2. GREEN player begins
3. Select a piece
4. Legal moves are highlighted
5. Select a destination
6. Board state and score are updated
7. Turn switches to the other player
8. Repeat until a player occupies the opponent's camp
9. Display final scores and game statistics
```

## Project Structure

```text
.
├── <game source files>
├── <supporting files>
├── README.md
└── screenshots/
```

The exact structure may vary depending on the final organization of the repository.

## Running the Game

Clone the repository:

```bash
git clone <repository-url>
cd <repository-directory>
```

Run the game using Python:

```bash
python <main-file>.py
```

The game can be configured for different board sizes and move time limits through the supported command-line parameters.

## Technical Concepts

This project demonstrates practical implementation of:

* Object-oriented programming
* Game-state management
* Graphical user interfaces
* Event-driven programming
* Coordinate systems
* Move generation
* Search over possible movement paths
* State validation
* Rule enforcement
* Turn-based state transitions
* Timer-based interaction
* Distance-based scoring
* Win-condition detection
* Data structure management

## Future Extensions

The architecture provides a foundation for extending the game beyond human-vs-human play.

Potential extensions include:

* Automated game-playing agents
* Minimax search
* Alpha-beta pruning
* Heuristic evaluation functions
* Human-vs-AI gameplay
* AI-vs-AI simulations
* Game replay functionality
* Performance benchmarking

---

### Technologies

**Python · Tkinter · Object-Oriented Programming · Game Development · GUI Programming · Algorithmic Move Generation · State Management.**
