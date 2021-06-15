# Getting started

This page should contain a short guide on what the plugin does and
a short example on how to use the plugin.

## Installation

Use the following commands to install the plugin:

    git clone https://github.com/aiidateam/aiida-restapi .
    cd aiida-restapi
    pip install -e .  # also installs aiida, if missing (but not postgres)
    #pip install -e .[pre-commit,testing] # install extras for more features
    verdi quicksetup  # better to set up a new profile
    verdi calculation plugins  # should now show your calclulation plugins

Then use ``verdi code setup`` with the ``restapi`` input plugin
to set up an AiiDA code for aiida-restapi.
