# GitHub Copilot Instructions for EasyReflectometryApp

## Project Overview

EasyReflectometryApp is a cross-platform desktop application for reflectometry data analysis, built with PySide6 (Qt6) for the GUI and Python for the backend. The app provides a tabbed workflow interface connecting to the EasyReflectometryLib scientific computing library.

## Architecture Overview

### QML/Python Hybrid Architecture
- **Frontend**: QML files define the user interface using Qt's declarative framework
- **Backend**: Python classes handle scientific computation via EasyReflectometryLib
- **Bridge**: PySide6 provides seamless QML-Python integration through property bindings and signals

Key architectural files:
- `EasyReflectometryApp/main.py` - Application entry point, registers PyBackend singleton
- `EasyReflectometryApp/Backends/Py/py_backend.py` - Central backend coordinator 
- `EasyReflectometryApp/Gui/Globals/BackendWrapper.qml` - QML singleton exposing backend API
- `EasyReflectometryApp/Gui/ApplicationWindow.qml` - Main application layout with workflow tabs

### Page-Based Workflow Architecture
The application follows a sequential workflow with these main pages:
1. **Home** - Project initialization and documentation
2. **Project** - Project metadata and settings  
3. **Sample** - Material and layer structure definition
4. **Experiment** - Data loading and instrument parameters
5. **Analysis** - Fitting and parameter refinement
6. **Summary** - Results reporting

Each page has its own backend class (`Home`, `Project`, `Sample`, `Experiment`, `Analysis`, `Summary`) coordinated by `PyBackend`.

### Data Flow Patterns
```
EasyReflectometryLib.Project ←→ PyBackend ←→ BackendWrapper.qml ←→ QML UI Components
```

Backend classes use Qt's Signal/Slot mechanism to propagate changes across pages. Critical connection points in `PyBackend._connect_backend_parts()`.

## Development Environment

- **Python**: 3.11, 3.12 (defined in pyproject.toml)
- **Qt Framework**: PySide6 6.8.x (avoid 6.9 due to TableView issues)
- **Platforms**: Windows, macOS, Linux Ubuntu
- **Dependencies**: EasyReflectometryLib, EasyApp (git dependencies)

### Installation from Source
```bash
git clone https://github.com/easyScience/EasyReflectometryApp
git clone https://github.com/easyScience/EasyApp  # Required peer dependency
cd EasyReflectometryApp
pip install -e .
python EasyReflectometryApp/main.py
```

## Code Style and Conventions

### Python Backend
- Follow **Ruff** configuration from pyproject.toml (line length 127, single quotes)
- Backend classes in `Backends/Py/` expose Qt Properties and Slots for QML access
- Logic implementation goes in `Backends/Py/logic/` subdirectory (not in main backend classes)
- Use PySide6 decorators: `@Property`, `@Signal`, `@Slot`

### QML Frontend  
- Use **EasyApp** components library for consistent UI (`import EasyApp.Gui.Elements as EaElements`)
- Access backend through `Globals.BackendWrapper` (never directly call `Backends.PyBackend`)
- Follow page structure: `Layout.qml` → `MainContent/` and `Sidebar/Basic/` folders
- Use `console.debug()` for logging (custom Qt message handler configured)
- Always test backend method availability before calling: `typeof Globals.BackendWrapper.methodName === 'function'`

### File Organization Patterns
```
EasyReflectometryApp/
├── Backends/Py/              # Python backend API
│   ├── {page}.py             # Page-specific backend (Sample, Analysis, etc)
│   └── logic/                # Business logic implementation
├── Gui/                      # QML user interface
│   ├── Globals/              # Singletons (BackendWrapper, References)
│   └── Pages/{Page}/         # Page-specific UI
│       ├── Layout.qml        # Main page layout
│       ├── MainContent/      # Central content area
│       └── Sidebar/Basic/    # Sidebar controls
└── main.py                   # Application entry point
```

## Testing and Development Workflow

### Running the Application
```bash
# Development mode
python EasyReflectometryApp/main.py

# Test mode (auto-quits after 30s)
python EasyReflectometryApp/main.py --testmode
```

### Debugging QML/Python Integration
- QML console messages appear in Python stdout (custom Qt message handler)
- Use `console.debug()` in QML, avoid `console.log()` for consistency
- Backend debugging via standard Python debugging tools
- Test backend method availability: `typeof Globals.BackendWrapper.methodName === 'function'`

### Building and Distribution
- **PyInstaller**: Creates standalone app bundles (configured in CI)
- **Qt Installer Framework**: Generates cross-platform installers  
- **GitHub Actions**: Automated building for all platforms in `.github/workflows/installer.yml`
- **Code Signing**: Windows (DigiCert KeyLocker), macOS (disabled but configured)

Build process: `tools/Scripts/FreezeApp.py` → `MakeInstaller.py` → `ZipAppInstaller.py`

## Critical Integration Points

### Backend Communication
- `PyBackend` uses `_connect_backend_parts()` to wire page dependencies
- Changes propagate via Qt signals: `externalSampleChanged`, `externalExperimentChanged`, etc.
- Plotting updates triggered by `_refresh_plots()` across multiple backend classes

### Adding New Python Methods/Properties - Complex Process
**CRITICAL**: Adding backend functionality requires updates in multiple locations:

1. **Logic Layer**: Add implementation in `Backends/Py/logic/{page}.py`
2. **Backend API**: Expose via `@Property` or `@Slot` in `Backends/Py/{page}.py`
3. **QML Bridge**: Add to `Gui/Globals/BackendWrapper.qml` property mapping
4. **Signal Connections**: Wire in `PyBackend._connect_{page}_page()` if state changes needed
5. **MockBackend**: Add parallel implementation in `Backends/Mock/{Page}.qml` for development

Example pattern from ExperimentalDataExplorer.qml:
```qml
// Test method availability before calling
if (typeof Globals.BackendWrapper.analysisSetSelectedExperimentIndices === 'function') {
    Globals.BackendWrapper.analysisSetSelectedExperimentIndices(selectedExperimentIndices)
} else {
    // Fallback approach or error handling
}
```

### MockBackend vs PyBackend
- Development uses `MockBackend.qml` when EasyReflectometryLib unavailable
- `BackendWrapper.qml` automatically selects backend at runtime
- Both backends must implement identical API for seamless switching

### Multi-Platform Considerations
- Path handling uses `pathlib.Path` for cross-platform compatibility
- Installer detection via `INSTALLER` boolean in main.py for different import paths
- Platform-specific CI configuration in pyproject.toml `[ci]` sections

## Common Development Patterns

### Adding New UI Components
1. Create QML file in appropriate `Pages/{Page}/` subfolder
2. Import via `Loader { source: 'Component.qml' }` pattern
3. Access backend through `Globals.BackendWrapper.{page}PropertyName`
4. Use EasyApp components for consistency

### Adding Backend Functionality  
1. Add logic to `Backends/Py/logic/` classes
2. Expose via `@Property` or `@Slot` in page backend class
3. Add to `BackendWrapper.qml` for QML access
4. Connect signals in `PyBackend._connect_{page}_page()` if needed

### Debugging QML/Python Integration
- QML console messages appear in Python stdout (custom Qt message handler)
- Backend debugging via standard Python debugging tools
- Use `console.debug()` in QML, avoid `console.log()` (inconsistent output)

### Common Integration Pitfalls
- **Method Availability**: Always check `typeof Globals.BackendWrapper.methodName === 'function'` before calling
- **Property Updates**: Changes to backend properties may not trigger QML updates without proper signal connections
- **Array Handling**: QML arrays passed to Python slots need explicit conversion (`list(indices)`)
- **Fallback Patterns**: Implement graceful degradation when backend methods aren't available yet

## Build System Details

The app uses a complex multi-step build process for professional distribution:
1. **Freeze**: PyInstaller bundles Python + dependencies into executable
2. **Package**: Qt IFW creates platform-native installers  
3. **Sign**: Code signing for Windows/macOS (production releases)
4. **Test**: Automated installation testing on all target platforms

Key build configuration in `pyproject.toml` `[ci]` section defines platform-specific settings.