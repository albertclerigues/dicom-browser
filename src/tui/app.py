from pydicom.dataset import Dataset
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Tree
from textual.widgets.tree import TreeNode

from src.dicom.loader import iter_dataset, load_dicom


class DicomTreeApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("left", "collapse_node", "Collapse"),
        ("right", "expand_node", "Expand"),
    ]

    def __init__(self, dicom_path: str):
        super().__init__()
        self.dicom_path = dicom_path

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Tree("DICOM Root")
        yield Footer()

    def on_mount(self) -> None:
        tree = self.query_one(Tree)
        tree.root.expand()

        try:
            ds = load_dicom(self.dicom_path)
            # Set root label to filename
            tree.root.label = f"FILE: {self.dicom_path}"
            self.populate_tree(tree.root, ds)
        except Exception as e:
            tree.root.add(f"[bold red]Error loading file:[/bold red] {e}")

    def populate_tree(self, node: TreeNode, dataset: Dataset) -> None:
        for tag, name, vr, value_str, raw_value in iter_dataset(dataset):
            # Format the label with fixed-width columns
            # Tag: 13 chars, Name: 40 chars, VR: 4 chars, Value: remaining
            tag_col = f"[bold #ff0055]{tag:<13}[/]"
            name_col = f"[bold]{name:<40}[/]"
            vr_col = f"[#00ffff]{vr:<4}[/]"
            value_col = f"[#ffff00]{value_str}[/]"

            label = f"{tag_col} {name_col} {vr_col} {value_col}"

            if vr == "SQ":
                child = node.add(label, expand=False)
                # Handle Sequence
                for i, item in enumerate(raw_value):
                    item_node = child.add(f"[bold]Item {i+1}[/]", expand=False)
                    self.populate_tree(item_node, item)
            else:
                node.add_leaf(label)

    def action_expand_node(self) -> None:
        """Expand the currently selected tree node."""
        tree = self.query_one(Tree)
        if tree.cursor_node and not tree.cursor_node.is_expanded:
            tree.cursor_node.expand()

    def action_collapse_node(self) -> None:
        """Collapse the currently selected tree node."""
        tree = self.query_one(Tree)
        if tree.cursor_node and tree.cursor_node.is_expanded:
            tree.cursor_node.collapse()
