all: build

build:
	cmake -B build -DCMAKE_BUILD_TYPE=Release -DECOSORT_FETCH_DEPS=ON
	cmake --build build --parallel

test:
	./build/test_correctness

smoke:
	mkdir -p results/raw
	./build/bench --smoke --trials 5 \
	    > results/raw/smoke_$$(date +%Y%m%dT%H%M%S).csv

full-study:
	python3 scripts/run_all.py --trials 30

analyze:
	python3 scripts/analyze.py --results-dir results
	python3 scripts/tables.py  --results-dir results
	python3 scripts/plots.py   --results-dir results
	python3 scripts/generate_results_summary.py results

reproduce:
	docker build -t ecosort-v2 .
	docker run --rm \
	    --privileged \
	    -v $$(pwd)/results:/ecosort/results \
	    ecosort-v2

clean:
	rm -rf build

.PHONY: all build test smoke full-study analyze reproduce clean

