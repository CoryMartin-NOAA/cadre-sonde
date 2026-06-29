#!/bin/bash

# Define the virtual environment directory
VENV_DIR="venv"

# Detect machine to set the correct spack-stack path
HOSTNAME=$(hostname)
if [[ "${HOSTNAME}" == *"ursa"* || "${HOSTNAME}" == *"ufe"* ]]; then
    MACHINE="ursa"
    SPACK_CORE="/contrib/spack-stack/spack-stack-1.9.2/envs/ue-oneapi-2024.2.1/install/modulefiles/Core"
elif [[ "${HOSTNAME}" == *"orion"* || "${HOSTNAME}" == *"Orion"* ]]; then
    MACHINE="orion"
    SPACK_CORE="/apps/contrib/spack-stack/spack-stack-1.9.2/envs/ue-oneapi-2024.1.0/install/modulefiles/Core"
elif [[ "${HOSTNAME}" == *"hercules"* || "${HOSTNAME}" == *"Hercules"* || "${HOSTNAME}" == *"hecs"* ]]; then
    MACHINE="hercules"
    SPACK_CORE="/apps/contrib/spack-stack/spack-stack-1.9.2/envs/ue-oneapi-2024.1.0/install/modulefiles/Core"
else
    echo "Unknown machine: ${HOSTNAME}. This script currently supports Ursa, Orion, and Hercules."
    exit 1
fi

echo "Detected machine: ${MACHINE}"
echo "Using spack-stack core: ${SPACK_CORE}"

# Use the spack-stack modulefiles path
module use ${SPACK_CORE}

# Load necessary modules for the base environment
module load stack-oneapi/2024.2.1
module load stack-intel-oneapi-mpi/2021.13
module load stack-python/3.11.7
module load py-pip/23.1.2

# Load Python dependencies available in spack-stack to avoid building from source
module load py-numpy/1.26.4
module load py-pandas/2.2.3
module load py-netcdf4/1.7.1.post2
module load py-xarray/2024.7.0
module load py-matplotlib/3.7.4

# Create the virtual environment using --system-site-packages so it inherits 
# the loaded py- modules from spack-stack
python3 -m venv --system-site-packages ${VENV_DIR}

# Activate the virtual environment
source ${VENV_DIR}/bin/activate

# Install the remaining requirements (like PyGSI) via pip
# Note: if the tag v1.0.0 is missing in the requirements.txt, you may need to update it
pip install -r requirements.txt

echo "Virtual environment created successfully in ${VENV_DIR}."
echo "To activate it, run: source ${VENV_DIR}/bin/activate"
echo "To create kernel:"
echo "pip install ipykernel"
echo "python -m ipykernel install --user --name=cadre --display-name="Python (cadre)"
