from typing import Tuple, Optional
import yaml
import os
from urllib.request import urlretrieve

from jkinpylib.robots import get_robot
from ikflow.utils import safe_mkdir, get_filepath
from ikflow.ikflow_solver import IkflowSolver
from ikflow.supporting_types import IkflowModelParameters
from ikflow.config import MODELS_DIR

with open(get_filepath("model_descriptions.yaml"), "r") as f:
    MODEL_DESCRIPTIONS = yaml.safe_load(f)


def download_model(url: str, download_dir: Optional[str] = None) -> str:
    """Download the model at the url `url` to the given directory. download_dir defaults to MODELS_DIR

    Args:
        model_url (str): _description_
        download_dir (str): _description_
    """
    if download_dir is None:
        download_dir = MODELS_DIR
    safe_mkdir(download_dir)
    assert os.path.isdir(download_dir), f"Download directory {download_dir} does not exist"
    model_name = model_filename(url)
    save_filepath = os.path.join(download_dir, model_name)
    if os.path.isfile(save_filepath):
        print(f"file '{save_filepath}' exists already - returning")
        return save_filepath
    urlretrieve(url, filename=save_filepath)  # returns (filename, headers)
    return save_filepath


def model_filename(url: str) -> str:
    """Return the model alias given the url of the model (stored in google cloud presumably).

    Example input/output: https://storage.googleapis.com/ikflow_models/atlas_desert-sweep-6.pkl -> atlas_desert-sweep-6.pkl
    """
    return url.split("/")[-1]


def get_ik_solver(model_name: str) -> Tuple[IkflowSolver, IkflowModelParameters]:
    """Build and return the `IkflowSolver` for the given model. The input `model_name` should match and index in `model_descriptions.yaml`

    Returns:
        Tuple[IkflowSolver, IkflowModelParameters]: A `IkflowSolver` solver and the corresponding
                                                            `IkflowModelParameters` parameters object
    """
    model_weights_url = MODEL_DESCRIPTIONS[model_name]["model_weights_url"]
    robot_name = MODEL_DESCRIPTIONS[model_name]["robot_name"]
    hparams = MODEL_DESCRIPTIONS[model_name]
    assert isinstance(robot_name, str), f"robot_name must be a string, got {type(robot_name)}"
    assert isinstance(hparams, dict), f"model_hyperparameters must be a Dict, got {type(hparams)}"

    model_weights_filepath = download_model(model_weights_url)
    assert os.path.isfile(
        model_weights_filepath
    ), f"File '{model_weights_filepath}' was not found. Unable to load model weights"

    robot = get_robot(robot_name)

    # Build IkflowSolver and set weights
    hyper_parameters = IkflowModelParameters()
    hyper_parameters.__dict__.update(hparams)
    ik_solver = IkflowSolver(hyper_parameters, robot)
    ik_solver.load_state_dict(model_weights_filepath)
    return ik_solver, hyper_parameters


if __name__ == "__main__":
    ik_solver, hyper_parameters = get_ik_solver("panda_tpm")
