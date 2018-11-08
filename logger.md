# GarageLogger

The current logger is simply a collection of global variables that needs to be replaced with a new class. I'm calling this new class **GarageLogger**.

I'm planning on using [jruere/multiprocessing-logging](https://github.com/jruere/multiprocessing-logging) to handle multiprocessing. This will make it much easier for all your processes to log to the same place. Essentially all it does is wrap a python logger so it plays well in a multiprocessing environment. GarageLogger will abstract away all of this so you don't have to worry about it.

The new logger will have add_text_output, add_tabular_output and add_tensorboard_output methods. Each output will be its own implementation of an **Output** abstract class, which will contain a multiprocessing logger.
