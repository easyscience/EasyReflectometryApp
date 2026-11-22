# Getting started
This is the tutorial for EasyReflectometryApp and how to use it.  
Version: 1.6.1

## Home page
When opening up the EasyRecletometryApp you are presented with the **Home** page.  

![Home page](./tutorials/_images/home.png)

- **A**: Starts your project.
- **B**: Pop-up window with source information.
- **C**: Link to developer documentation.

## Intialise project

Pressing **A** will direct you to the **Project** page.  

![Project overview](./tutorials/_images/project.png)

- **1**: Create a new project as a folder containing experiments and a JSON file for settings.
   - New projects need a name, description and set the save location.
- **2**: Opens a previous project from the JSON file.
- **3**: Continues to the next page, here it is **Model**.
    - This button is universal throughout the app and will always forward you to the next page.


If no project is selected/created a default project is initialised.  
This project is used going forward to explain the app.

### Creating a new project
**Create a new project** opens a dialog for the name, description and location of the
project. **OK** creates it; **Cancel** closes the dialog and creates nothing.

When the session already holds a sample, data or fit settings of your own - built before
any project existed, or belonging to the project that is open - the app first asks what the
new project should start with:

- **Keep sample and data**: the new project starts with what is on screen.
- **Start from scratch**: the new project starts with the default sample and no data.
- **Cancel**: no new project.

The dialog also says whether the current work has been saved. Starting from scratch
discards work that was never saved to a project. Nothing is reset until the new project's
details are confirmed with **OK**, so cancelling there keeps everything as it was.

```{note}
Projects saved by EasyReflectometry 1.5 or earlier cannot be opened by later versions.
Re-create them, or open them with EasyReflectometry 1.5.
```

## Save and settings
When a project is started two further buttons is visualised, and settings is the opposite corner of those.

![Save Settings](./tutorials/_images/save_setting.png)

- **A**: Save project.
- **B**: Reset to start.
- **C**: Setting, is further explained in settings.

### Automatic saving
Once a project has been created, the app also saves it without being asked, whenever it has
unsaved changes at one of these moments:

- when you leave a page;
- after a successful fit, and after a Bayesian sampling run;
- just before a fit starts, before the calculation engine is switched, and before the
  sample is replaced by one loaded from an ORSO file.

Nothing is saved automatically while a fit is running.

Each automatic save first copies the project file it replaces to `project.json.bak` in the
project folder, so one unwanted automatic save can be undone by hand. Saving with the save
button (**A**) does not write a backup.

The **Saved** item of the status bar gives the time of the last save, followed by `(auto)`
when that save was automatic; its tooltip then gives the path of the backup. If an
automatic save fails, a dialog says so once and the status bar shows **Autosave failed**
until a save succeeds. Your work is still in memory: use the save button to retry.

To switch automatic saving off, untick **Save automatically** in the **Saving** group of
the `Advanced controls` of the `Project` page. The choice is an application preference: it
is remembered between sessions and applies to every project.

## Sample structure view
The **Model** page has a **Structure** tab next to **Reflectivity** showing a schematic of
the current model's layer stack: one colored box per layer, ambient medium on top, substrate
at the bottom. Boxes share a color per material (see the legend), box heights follow layer
thickness, and repeated multilayers with many repetitions are drawn once with a "× N" badge.

Hover a box for its material, SLD, thickness and roughness; click it to select that layer in
the sidebar editor. The view updates immediately when the model changes, including after a fit.

Note the view is a schematic, not a to-scale cross-section: heights are clamped so very thin
layers stay visible and very thick ones do not crowd out the rest.
