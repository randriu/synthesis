#!/bin/bash

MODEL=testing-rewards.prism
FOLDER=testing-rewards

PREFIX=models/posmg
PRISM=prism-models

./prerequisites/prism-games $PREFIX/$PRISM/$MODEL -exportmodel sketch.drn
mv sketch.drn $PREFIX/$FOLDER/sketch.templ
