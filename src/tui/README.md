# Cognitive Orchestration Stack TUI

A sophisticated Terminal User Interface (TUI) for the Cognitive Orchestration Stack, built with Textual.

## Features

- **Main Menu**: Intuitive navigation hub with OptionList
- **Query Interface**: Interactive chat with the AI agent
- **Data Ingestion**: File, directory, and URL data processing
- **ARIS Research**: Automated research task execution
- **System Status**: Real-time health monitoring and metrics

## Quick Start

### Installation

```bash
# Install dependencies
poetry install

# Launch the TUI
poetry run cos
```

### Manual Launch

```bash
# Using Python module
python -m src.tui.app

# Using direct import
python -c "from src.tui.app import main; main()"
```

## Navigation

- **Arrow Keys**: Navigate menus and options
- **Enter**: Select/confirm actions
- **Tab**: Move between input fields
- **B**: Go back to main menu (from any screen)
- **Q**: Quit application
- **Ctrl+C**: Quit application

## Screen Descriptions

### Main Menu

Central navigation hub with options for all major features.

### Query Screen

- Type queries in the input field
- View conversation history in the scrollable log
- Agent responses appear in real-time

### Ingest Screen

- Select data source type (File/Directory/URL)
- Enter path or URL
- Monitor progress with real-time progress bar
- View status updates

### ARIS Screen

- Enter research topic
- Watch step-by-step research progress
- View detailed logs of research activities
- Access final research results

### Status Screen

- Monitor system health components
- View real-time resource usage
- Check service status
- Refresh data with R key

## Integration Points

The TUI is designed to integrate with your existing backend services:

- **Query Processing**: `src.orchestration.graph.run_query()`
- **Data Ingestion**: `src.scripts.ingest_data.run_ingestion()`
- **ARIS Research**: `src.scripts.run_aris_job.run_aris_research()`
- **Health Checks**: `src.api.health.check_health()`

## Customization

### Styling

Edit `src/tui/cos.tcss` to customize the appearance:

- Colors and themes
- Layout and spacing
- Component styling

### Adding Screens

1. Create new screen class in `src/tui/screens/`
2. Add to `SCREENS` dictionary in `src/tui/app.py`
3. Update navigation in main menu

### Backend Integration

Replace placeholder functions in each screen with actual backend calls:

- Use `self.run_worker()` for long-running operations
- Use `self.call_from_thread()` to update UI from workers
- Handle errors gracefully with try/catch blocks

## Development

### Running Tests

```bash
python test_tui_integration.py
```

### Code Style

The project follows PEP 8 with line length of 79 characters:

```bash
# Format code
poetry run format

# Check linting
poetry run lint

# Type checking
poetry run type-check
```

## Troubleshooting

### Common Issues

1. **CSS Errors**: Ensure `cos.tcss` uses valid Textual CSS properties
2. **Import Errors**: Verify all dependencies are installed with `poetry install`
3. **Screen Navigation**: Check that screens are properly registered in `SCREENS`

### Debug Mode

Set environment variable for verbose logging:

```bash
export TEXTUAL_LOG=1
poetry run cos
```

## Architecture

```text
src/tui/
├── app.py              # Main application entry point
├── cos.tcss           # Global styling
├── screens/           # Screen implementations
│   ├── main_menu.py   # Main navigation
│   ├── query.py       # AI agent interface
│   ├── ingest.py      # Data ingestion
│   ├── aris.py        # Research tasks
│   └── status.py      # System monitoring
└── README.md          # This file
```

## License

All Rights Reserved - funkyflowstudios
