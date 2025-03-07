# Models API Reference

This section documents the model classes used in the Forest Dashboard application.

## Plot Model

The Plot Model handles creating and updating plots based on the grammar of graphics state.

```python
from bosques_app.models.plot_model import PlotModel
```

::: bosques_app.models.plot_model.PlotModel
    options:
      members:
        - update_plot
        - _create_scatter_plot
        - _create_line_plot
        - _create_bar_plot
        - _connect_legend_toggling
      show_root_heading: true
      show_source: true

## Data Model

The Data Model handles loading and processing Excel data.

```python
from bosques_app.models.data_model import DataModel
```

::: bosques_app.models.data_model.DataModel
    options:
      members:
        - load_excel
        - create_unified_dataframe
        - get_summary
      show_root_heading: true
      show_source: true
