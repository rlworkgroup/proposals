# GarageLogger
Proposal by Peter Lillian

## Background

The current logger is simply a collection of global variables that needs to be replaced with a new object-oriented API that is easier to work with. I'm calling this new class **GarageLogger**.

**Problem Statement**
The logger interface is a bolt-on, package-gobal mess that isn't multiprocess-aware and fails to conform to garage code 

**Scope**
This PR encompasses creating a usable logger API for garage that is easily extensible and editable.

**Goals**
- Remove global scope
- Wrap logger into singleton class
- Define simple API
- Decouple frontend and backend

**Non-Goals**
- Make the logger 

## Design Overview

**Inputs**
Text, Key-Value, Snapshots, distributions, etc

**Outputs**

![GarageLogger](GarageLogger.svg)

Each output will be its own implementation of an **OutputType** abstract class, which will contain a multiprocessing logger and handle writing to any outputs assigned. GarageLogger will keep a dictionary of the current OutputTypes. For example: **TextOutput**, **TabularOutput**, or **TensorboardOutput**

It will also of course have a `log` method which takes the data to be sent to the logger. The logger will attempt to send the output to all OutputType specified during configuration

The logger will also have python's standard `debug`, `info`, `warning`, and `error` methods, which will log to the text output by default.

It will retain functionality such as the prefix stack from the old logger.
