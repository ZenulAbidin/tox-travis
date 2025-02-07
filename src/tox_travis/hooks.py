"""Tox hook implementations."""
from __future__ import print_function
import os
import sys
import tox
from tox.plugin import impl
from .envlist import (
    detect_envlist,
    autogen_envconfigs,
    override_ignore_outcome,
)
from .hacks import (
    pypy_version_monkeypatch,
    subcommand_test_monkeypatch,
)
from .after import travis_after


@impl
def tox_add_option(parser):
    """Add arguments and needed monkeypatches."""
    parser.add_argument(
        '--travis-after', dest='travis_after', action='store_true',
        help='Exit successfully after all Travis jobs complete successfully.')

    if 'TRAVIS' in os.environ:
        pypy_version_monkeypatch()
        subcommand_test_monkeypatch(tox_subcommand_test_post)


@impl
def tox_add_env_config(env_conf, state):
    """Check for the presence of the added options."""
    if 'TRAVIS' not in os.environ:
        return

    config = env_conf
    ini = config._cfg

    # envlist
    if 'TOXENV' not in os.environ and not config.option.env:
        envlist = detect_envlist(ini)
        undeclared = set(envlist) - set(config.envconfigs)
        if undeclared:
            print('Matching undeclared envs is deprecated. Be sure all the '
                  'envs that Tox should run are declared in the tox config.',
                  file=sys.stderr)
            autogen_envconfigs(config, undeclared)
        # Also set envlist_default to allow us to inspect outcomes
        # via tox -l in the tests, until a better solution arrives.
        config.envlist_default = config.envlist = envlist

    # Override ignore_outcomes
    if override_ignore_outcome(ini):
        for envconfig in config.envconfigs.values():
            envconfig.ignore_outcome = False

    # after
    if config.option.travis_after:
        print('The after all feature has been deprecated. Check out Travis\' '
              'build stages, which are a better solution. '
              'See https://tox-travis.readthedocs.io/en/stable/after.html '
              'for more details.', file=sys.stderr)


def tox_subcommand_test_post(config):
    """Wait for this job if the configuration matches."""
    if config.option.travis_after:
        travis_after(config._cfg, config.envlist)
