from pathlib import Path

import arviz as az
import bambi as bmb
import numpy as np
import pandas as pd
import pytensor
import pytest
import ssms

from hssm import HSSM
from hssm.hssm import _model_has_default
from hssm.utils import download_hf
from hssm.likelihoods import DDM, logp_ddm

pytensor.config.floatX = "float32"


@pytest.fixture
def data():
    v_true, a_true, z_true, t_true = [0.5, 1.5, 0.5, 1.5]
    obs_ddm = ssms.basic_simulators.simulator(
        [v_true, a_true, z_true, t_true], model="ddm", n_samples=50
    )
    obs_ddm = np.column_stack([obs_ddm["rts"][:, 0], obs_ddm["choices"][:, 0]])
    dataset = pd.DataFrame(obs_ddm, columns=["rt", "response"])
    dataset["x"] = dataset["rt"] * 0.1
    dataset["y"] = dataset["rt"] * 0.5
    return dataset


@pytest.fixture(scope="module")
def fixture_path():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def data_angle():
    v_true, a_true, z_true, t_true, theta_true = [0.5, 1.5, 0.5, 0.5, 0.3]
    obs_angle = ssms.basic_simulators.simulator(
        [v_true, a_true, z_true, t_true, theta_true], model="angle", n_samples=100
    )
    obs_angle = np.column_stack([obs_angle["rts"][:, 0], obs_angle["choices"][:, 0]])
    data = pd.DataFrame(obs_angle, columns=["rt", "response"])
    return data


@pytest.fixture
def example_model_config():
    return {
        "loglik_kind": "example",
        "list_params": ["v", "a", "z", "t"],
        "bounds": {
            "v": (-3.0, 3.0),
            "a": (0.3, 2.5),
            "z": (0.1, 0.9),
            "t": (0.0, 2.0),
        },
    }


@pytest.mark.parametrize(
    "include, should_raise_exception",
    [
        (
            [
                {
                    "name": "v",
                    "prior": {
                        "Intercept": {"name": "Uniform", "lower": -3.0, "upper": 3.0},
                        "x": {"name": "Uniform", "lower": -0.50, "upper": 0.50},
                        "y": {"name": "Uniform", "lower": -0.50, "upper": 0.50},
                    },
                    "formula": "v ~ 1 + x + y",
                    "link": "identity",
                }
            ],
            False,
        ),
        (
            [
                {
                    "name": "v",
                    "prior": {
                        "Intercept": {"name": "Uniform", "lower": -2.0, "upper": 3.0},
                        "x": {"name": "Uniform", "lower": -0.50, "upper": 0.50},
                        "y": {"name": "Uniform", "lower": -0.50, "upper": 0.50},
                    },
                    "formula": "v ~ 1 + x + y",
                },
                {
                    "name": "a",
                    "prior": {
                        "Intercept": {"name": "Uniform", "lower": -2.0, "upper": 3.0},
                        "x": {"name": "Uniform", "lower": -0.50, "upper": 0.50},
                        "y": {"name": "Uniform", "lower": -0.50, "upper": 0.50},
                    },
                    "formula": "a ~ 1 + x + y",
                },
            ],
            False,
        ),
        (
            [{"name": "invalid_param", "prior": "invalid_param"}],
            True,
        ),
        (
            [
                {
                    "name": "v",
                    "prior": {
                        "Intercept": {"name": "Uniform", "lower": -3.0, "upper": 3.0}
                    },
                    "formula": "v ~ 1",
                    "invalid_key": "identity",
                }
            ],
            True,
        ),
        (
            [
                {
                    "name": "v",
                    "prior": {
                        "Intercept": {"name": "Uniform", "lower": -3.0, "upper": 3.0}
                    },
                    "formula": "invalid_formula",
                }
            ],
            True,
        ),
    ],
)
def test_transform_params_general(data, include, should_raise_exception):
    if should_raise_exception:
        with pytest.raises(Exception):
            HSSM(data=data, include=include)
    else:
        model = HSSM(data=data, include=include)
        # Check model properties using a loop
        param_names = ["v", "a", "z", "t", "p_outlier"]
        model_param_names = list(model.params.keys())
        assert model_param_names == param_names
        assert len(model.params) == 5


def test__model_has_default():
    assert _model_has_default("ddm", "analytical")
    assert not _model_has_default("ddm", "blackbox")
    assert not _model_has_default("custom", "analytical")


def test_custom_model(data, example_model_config):
    with pytest.raises(
        ValueError, match="When using a custom model, please provide a `loglik_kind.`"
    ):
        model = HSSM(data=data, model="custom")

    with pytest.raises(ValueError, match="Please provide a valid `loglik`."):
        model = HSSM(data=data, model="custom", loglik_kind="analytical")

    with pytest.raises(
        ValueError, match="For custom models, please provide a valid `model_config`."
    ):
        model = HSSM(data=data, model="custom", loglik=DDM, loglik_kind="analytical")

    with pytest.raises(
        ValueError,
        match="For custom models, please provide `list_params` in `model_config`.",
    ):
        model = HSSM(
            data=data,
            model="custom",
            loglik=DDM,
            loglik_kind="analytical",
            model_config={},
        )

    model = HSSM(
        data=data,
        model="custom",
        model_config=example_model_config,
        loglik=logp_ddm,
        loglik_kind="analytical",
    )

    assert model.model_name == "custom"
    assert model.loglik_kind == "analytical"
    assert model.list_params == example_model_config["list_params"]


def test_model_definition_outside_include(data):
    model_with_one_param_fixed = HSSM(data, a=0.5)

    assert "a" in model_with_one_param_fixed.priors
    assert model_with_one_param_fixed.priors["a"] == 0.5

    model_with_one_param = HSSM(
        data, a={"prior": {"name": "Normal", "mu": 0.5, "sigma": 0.1}}
    )

    assert "a" in model_with_one_param.priors
    assert model_with_one_param.priors["a"].name == "Normal"

    with pytest.raises(
        ValueError, match='Parameter "a" is already specified in `include`'
    ):
        HSSM(data, include=[{"name": "a", "prior": 0.5}], a=0.5)


def test_model_with_approx_differentiable_likelihood_type(data_angle):
    loglik_kind = "approx_differentiable"
    loglik = "angle.onnx"
    model = HSSM(data=data_angle, model="angle", loglik_kind=loglik_kind, loglik=loglik)
    assert model.loglik == download_hf(loglik)


def test_sample_prior_predictive(data):
    data = data.iloc[:10, :]

    model_no_regression = HSSM(data=data)
    rng = np.random.default_rng()

    prior_predictive_1 = model_no_regression.sample_prior_predictive(draws=10)
    prior_predictive_2 = model_no_regression.sample_prior_predictive(
        draws=10, random_seed=rng
    )

    model_regression = HSSM(data=data, include=[dict(name="v", formula="v ~ 1 + x")])
    prior_predictive_3 = model_regression.sample_prior_predictive(draws=10)

    model_regression_a = HSSM(data=data, include=[dict(name="a", formula="a ~ 1 + x")])
    prior_predictive_4 = model_regression_a.sample_prior_predictive(draws=10)

    model_regression_multi = HSSM(
        data=data,
        include=[
            dict(name="v", formula="v ~ 1 + x"),
            dict(name="a", formula="a ~ 1 + y"),
        ],
    )
    prior_predictive_5 = model_regression_multi.sample_prior_predictive(draws=10)

    data["subject_id"] = np.arange(10)

    model_regression_random_effect = HSSM(
        data=data,
        include=[
            dict(name="v", formula="v ~ (1|subject_id) + x"),
            dict(name="a", formula="a ~ (1|subject_id) + y"),
        ],
    )
    prior_predictive_6 = model_regression_random_effect.sample_prior_predictive(
        draws=10
    )


def test_hierarchical(data):
    data = data.iloc[:10, :].copy()
    data["participant_id"] = np.arange(10)

    model = HSSM(data=data)
    assert all(
        param.is_regression
        for name, param in model.params.items()
        if name != "p_outlier"
    )

    model = HSSM(data=data, v=bmb.Prior("Uniform", lower=-10.0, upper=10.0))
    assert all(
        param.is_regression
        for name, param in model.params.items()
        if name not in ["v", "p_outlier"]
    )

    model = HSSM(data=data, a=bmb.Prior("Uniform", lower=0.0, upper=10.0))
    assert all(
        param.is_regression
        for name, param in model.params.items()
        if name not in ["a", "p_outlier"]
    )

    model = HSSM(
        data=data,
        v=bmb.Prior("Uniform", lower=-10.0, upper=10.0),
        a=bmb.Prior("Uniform", lower=0.0, upper=10.0),
    )
    assert all(
        param.is_regression
        for name, param in model.params.items()
        if name not in ["v", "a", "p_outlier"]
    )
