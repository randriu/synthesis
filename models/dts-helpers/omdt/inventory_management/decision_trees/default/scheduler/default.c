#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[0] <= 39.5) {
		if (x[0] <= 7.5) {
			if (x[0] <= 3.5) {
				if (x[0] <= 1.5) {
					if (x[0] <= 0.5) {
						return 0.0f;
					}
					else {
						return 1.0f;
					}

				}
				else {
					if (x[0] <= 2.5) {
						return 2.0f;
					}
					else {
						return 3.0f;
					}

				}

			}
			else {
				if (x[0] <= 5.5) {
					if (x[0] <= 4.5) {
						return 4.0f;
					}
					else {
						return 5.0f;
					}

				}
				else {
					if (x[0] <= 6.5) {
						return 6.0f;
					}
					else {
						return 7.0f;
					}

				}

			}

		}
		else {
			if (x[0] <= 9.5) {
				if (x[0] <= 8.5) {
					return 8.0f;
				}
				else {
					return 9.0f;
				}

			}
			else {
				if (x[0] <= 20.5) {
					if (x[0] <= 18.5) {
						return 10.0f;
					}
					else {
						if (x[0] <= 19.5) {
							return 8.0f;
						}
						else {
							return 9.0f;
						}

					}

				}
				else {
					return 10.0f;
				}

			}

		}

	}
	else {
		return 11.0f;
	}

}