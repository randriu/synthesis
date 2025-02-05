#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[1] <= 1.5) {
		if (x[2] <= 2.5) {
			if (x[0] <= 3.0) {
				return 0.0f;
			}
			else {
				return 6.0f;
			}

		}
		else {
			return 1.0f;
		}

	}
	else {
		if (x[5] <= 166.5) {
			if (x[6] <= 35.5) {
				if (x[5] <= 55.5) {
					return 2.0f;
				}
				else {
					if (x[0] <= 4.5) {
						if (x[1] <= 4.5) {
							if (x[4] <= 84.5) {
								return 2.0f;
							}
							else {
								return 3.0f;
							}

						}
						else {
							return 3.0f;
						}

					}
					else {
						if (x[1] <= 4.5) {
							if (x[2] <= 0.5) {
								return 2.0f;
							}
							else {
								return 4.0f;
							}

						}
						else {
							return 2.0f;
						}

					}

				}

			}
			else {
				return 5.0f;
			}

		}
		else {
			if (x[0] <= 5.5) {
				return 3.0f;
			}
			else {
				return 4.0f;
			}

		}

	}

}