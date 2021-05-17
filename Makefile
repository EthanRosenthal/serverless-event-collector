all: collector fan_out authorizer

clean:
	make -C collector clean
	make -C fan_out clean
	make -C authorizer clean

collector:
	make -C collector

fan_out:
	make -C fan_out

authorizer:
	make -C authorizer


.PHONY: all clean collector fan_out authorizer
