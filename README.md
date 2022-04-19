# 2021-2-MeasureSoftGram-Service

[![codecov](https://codecov.io/gh/fga-eps-mds/2021-2-MeasureSoftGram-Service/branch/develop/graph/badge.svg?token=XRPXP8LH9I)](https://app.codecov.io/gh/fga-eps-mds/2021-2-MeasureSoftGram-service/)

# What is it?

The MeasureSoftGram-Service is responsible for containing and manipulating MeasureSoftGram data: metrics, configuration goals, analyzes performed, etc. It uses the MVC layer pattern for building and organizing the service.

# How to execute
-[How to use](https://fga-eps-mds.github.io/2021-2-MeasureSoftGram-Doc/docs/artifact/how_to_use)

# How to run Service

First build the images in the docker with :

```
docker-compose build
```

Then made the container with :

```
docker-compose up
```

# How to run tests
Install this packages

```
pip install .
```

```
pip install -r requirements.txt
```


We are using tox for the tests, so it is good to install the tox:

```
pip install tox
```

Then you can run the tests using
```
 tox <PACKAGE OR ARCHIVE>
```

If it does not work, you can try to run before: 
```
pip install pytest-mock
```

# Another informations

Our services are available on [Docker Hub](https://hub.docker.com/):
- [Core](https://hub.docker.com/r/measuresoftgram/core)
- [Service](https://hub.docker.com/r/measuresoftgram/service)

## Wiki
- [Wiki](https://fga-eps-mds.github.io/2021-2-MeasureSoftGram-Doc/).

# Contribute

Do you want to contribute with our project? Access our [contribution guide](https://github.com/fga-eps-mds/2021-2-MeasureSoftGram-Service/blob/develop/CONTRIBUTING.md) where we explain how you do it.

# License

AGPL-3.0 License

# Documentation

The documentation of this project can be accessed at this website: [Documentation](https://github.com/fga-eps-mds/2021-2-MeasureSoftGram-Doc).
