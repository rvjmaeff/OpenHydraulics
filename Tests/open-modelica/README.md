# Automated development testing for Open Modelica

This library is tested with the open-modelica build specified in the dockerfile, using OMPython to call the *.mos scripts specifying the simulation paramters like startTime, stopTime, and solver. These scripts use the OMC scripting API.

Each *.mos script should be in the following form.
```
simulate(
    ModelPathInPackage, // e.g. OpenHydraulics.DevelopmentTests.AirChamberTest
    startTime=0,
    stopTime=1,
    numberOfIntervals=500,
    tolerance=1e-6,
    method="dassl"
    );
```

To run the tests:

```
# From the project root
docker-compose run open-modelica python3 \
/usr/src/OpenHydraulics/Tests/open-modelica/batch.py \
/usr/src/OpenHydraulics/OpenHydraulics/package.mo \
--input /usr/src/OpenHydraulics/Tests/open-modelica/scripts \
--log /usr/src/OpenHydraulics \
# --output /usr/src/OpenHydraulics/Results # if you want to keep the generated code and results files
```

For more options:

```
docker-compose run open-modelica python3 \
/usr/src/OpenHydraulics/Tests/open-modelica/batch.py --help
```

# TODO
Store the baseline csv/mat results and compare for regression testing.