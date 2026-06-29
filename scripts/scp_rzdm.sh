#!/bin/bash


PDY=20260629
cyc=00

wcoss_file=/lfs/h1/ops/prod/com/gfs/v16.3/gdas.${PDY}/${cyc}/atmos/gdas.t${cyc}z.cnvstat

rzdm_user=cmartin
rzdm_dir=/home/www/emc/htdocs/users/cmartin/cadre

scp -r $wcoss_file $rzdm_user@emcrzdm.ncep.noaa.gov:$rzdm_dir/.
