<div style="position: relative; width: 100%;">
  <img src="images/mainlogo.png" style="width: 250px;">
  <a href="https://ccbs.carney.brown.edu/brainstorm" style="position: absolute; right: 0; top: 50%; transform: translateY(-50%);">
    <img src="images/Brain-Bolt-%2B-Circuits.gif" style="width: 100px;">
  </a>
</div>

HSSM is a Python toolbox that provides a seamless combination of state-of-the-art likelihood approximation methods with the wider ecosystem of probabilistic programming languages. It facilitates flexible hierarchical model building and inference via modern MCMC samplers. HSSM is user-friendly and provides the ability to rigorously estimate the impact of neural and other trial-by-trial covariates through parameter-wise mixed-effects models for a large variety of cognitive process models.

**Authors**: Alexander Fengler, Aisulu Omar, Paul Xu, Krishn Bera, Michael J. Frank

**Contacts**: alexander_fengler@brown.edu

**Github**: https://github.com/lnccbrown/HSSM

**Copyright**: This document has been placed in the public domain.

**License**: HSSM is licensed under [Copyright 2023, Brown University, Providence, RI](../LICENSE)

**Version**: 0.1.2

- Allows approximate hierarchical Bayesian inference via various likelihood approximators.
- Estimate impact of neural and other trial-by-trial covariates via native hierarchical mixed-regression support.
- Extensible for users to add novel models with corresponding likelihoods.
- Built on PyMC with support from the Python Bayesian ecosystem at large.
- Incorporates Bambi's intuitive `lmer`-like regression parameter specification for within- and between-subject effects.
- Native ArviZ support for plotting and other convenience functions to aid the Bayesian workflow.
- Utilizes the ONNX format for translation of differentiable likelihood approximators across backends.

## Installation

`hssm` is available through PyPI. You can install it with Pip via:

```
pip install hssm
```

You can also install the bleeding edge version of `hssm` directly from this repo:

```
pip install git+https://github.com/lnccbrown/HSSM.git
```

For more detailed guidance, please check out our [installation guide](installation.md).

!!! note

    Possible solutions to any issues with installations with hssm can be located
    [here](https://github.com/lnccbrown/HSSM/discussions). We recommend leveraging an
    environment manager with Python 3.9~3.11 to prevent any problems with dependencies
    during the installation process. Please note that hssm is tested for python 3.9, 3.10,
    3.11. Use other python versions with caution.

### Setting global float type

Using the analytical DDM (Drift Diffusion Model) likelihood in PyMC without forcing float type to `"float32"` in PyTensor may result in warning messages during sampling, which is a known bug in PyMC v5.6.0 and earlier versions. We can use `hssm.set_floatX("float32")` to get around this for now.

```python
hssm.set_floatX("float32")
```

## Example

Here is a simple example of how to use HSSM:

```python
import hssm

# Set float type to float32 to avoid a current bug in PyMC mentioned above
# This will not be necessary in the future
hssm.set_floatX("float32")

# Load a package-supplied dataset
cav_data = hssm.load_data('cavanagh_theta')

# Define a basic hierarchical model with trial-level covariates
model = hssm.HSSM(
    model="ddm",
    data=cav_data,
    include=[
        {
            "name": "v",
            "prior": {
                "Intercept": {"name": "Uniform", "lower": -3.0, "upper": 3.0},
                "theta": {"name": "Uniform", "lower": -1.0, "upper": 1.0},
            },
            "formula": "v ~ (1|subj_idx) + theta",
            "link": "identity",
        },
    ],
)

# Sample from the posterior for this model
model.sample()
```

## License

HSSM is licensed under [Copyright 2023, Brown University, Providence, RI](LICENSE)

## Support

For questions, bug reports, or other unexpected issues, please open an issue on the GitHub repository.

## Contributing

If you want to contribute to this project, please familiarize yourself with our [contribution guidelines](CONTRIBUTING.md).
