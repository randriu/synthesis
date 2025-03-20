#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,5.f,5.f,3.f,1.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[2] <= 0.5) {
		return 0.0f;
	}
	else {
		if (x[1] <= 0.5) {
			if (x[5] <= 4.5) {
				return 1.0f;
			}
			else {
				return 2.0f;
			}

		}
		else {
			if (x[5] <= 3.5) {
				return 2.0f;
			}
			else {
				if (x[5] <= 4.5) {
					if (x[6] <= 3.5) {
						return 3.0f;
					}
					else {
						return 2.0f;
					}

				}
				else {
					return 3.0f;
				}

			}

		}

	}

}