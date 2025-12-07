from pydicom.dataset import Dataset
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Tree
from textual.widgets.tree import TreeNode

from src.dicom.loader import iter_dataset, load_dicom


class DicomTreeApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [("q", "quit", "Quit")]

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
            # Format the label with some colors using rich markup
            # Tag in pink, VR in cyan, Value in yellow
            label = f"[bold #ff0055]{tag}[/] [bold]{name}[/] ([#00ffff]{vr}[/]): [#ffff00]{value_str}[/]"

            if vr == "SQ":
                child = node.add(label, expand=False)
                # Handle Sequence
                for i, item in enumerate(raw_value):
                    item_node = child.add(f"[bold]Item {i+1}[/]", expand=False)
                    self.populate_tree(item_node, item)
            else:
                node.add_leaf(label)
