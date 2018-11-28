# GarageLogger
Proposal by Peter Lillian

## Background

The current logger is simply a collection of global variables that needs to be replaced with a new object-oriented API that is easier to work with. The class will simply be called **Logger**.

**Problem Statement**
A good logger should support many different input types and flawlessly handle all of them in a single data structure. It should send its data to multiple outputs and easily be extensible with new classes and features.

**Goals**
- Singleton logger class
- Simple API
- Single data structure for all types of logs
- Support for multiple inputs
- Support for multiple outputs simultaneously

**Non-Goals**
- Multiprocessing-awareness

## Design Overview

**Inputs**

Text, Key-Value, Snapshots, distributions, etc

**Outputs**

Each output will be its own implementation of an **LoggerOutput** abstract class, which will contain a multiprocessing logger and handle writing to any outputs assigned. GarageLogger will keep a dictionary of the current OutputTypes. For example: **TextOutput**, **TabularOutput**, or **TensorboardOutput**

It will also of course have a `log` method which takes the data to be sent to the logger. The logger will attempt to send the output to all OutputType specified during configuration

The logger will also have python's standard `debug`, `info`, `warning`, and `error` methods, which will log to the text output by default.

It will retain functionality such as the prefix stack from the old logger.
