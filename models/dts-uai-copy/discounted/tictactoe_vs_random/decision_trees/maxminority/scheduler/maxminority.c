#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {1.f,0.f,0.f,0.f,1.f,0.f,1.f,0.f,0.f,0.f,0.f,1.f,0.f,0.f,1.f,0.f,0.f,1.f,1.f,0.f,0.f,0.f,1.f,0.f,0.f,1.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[18] <= 0.5) {
		if (x[21] <= 0.5) {
			if (x[22] <= 0.5) {
				if (x[9] <= 0.5) {
					if (x[25] <= 0.5) {
						return 7.0f;
					}
					else {
						return 3.0f;
					}

				}
				else {
					if (x[19] <= 0.5) {
						return 4.0f;
					}
					else {
						return 3.0f;
					}

				}

			}
			else {
				return 4.0f;
			}

		}
		else {
			if (x[16] <= 0.5) {
				if (x[13] <= 0.5) {
					if (x[7] <= 0.5) {
						if (x[9] <= 0.5) {
							return 6.0f;
						}
						else {
							return 5.0f;
						}

					}
					else {
						if (x[15] <= 0.5) {
							return 6.0f;
						}
						else {
							return 0.0f;
						}

					}

				}
				else {
					if (x[0] <= 0.5) {
						return 8.0f;
					}
					else {
						return 2.0f;
					}

				}

			}
			else {
				if (x[10] <= 0.5) {
					if (x[6] <= 0.5) {
						return 5.0f;
					}
					else {
						return 1.0f;
					}

				}
				else {
					if (x[12] <= 0.5) {
						return 0.0f;
					}
					else {
						return 2.0f;
					}

				}

			}

		}

	}
	else {
		if (x[10] <= 0.5) {
			if (x[6] <= 0.5) {
				if (x[3] <= 0.5) {
					if (x[16] <= 0.5) {
						return 1.0f;
					}
					else {
						return 5.0f;
					}

				}
				else {
					if (x[7] <= 0.5) {
						return 5.0f;
					}
					else {
						if (x[9] <= 0.5) {
							return 1.0f;
						}
						else {
							return 6.0f;
						}

					}

				}

			}
			else {
				if (x[4] <= 0.5) {
					return 2.0f;
				}
				else {
					if (x[12] <= 0.5) {
						return 0.0f;
					}
					else {
						return 1.0f;
					}

				}

			}

		}
		else {
			if (x[3] <= 0.5) {
				if (x[16] <= 0.5) {
					return 2.0f;
				}
				else {
					return 0.0f;
				}

			}
			else {
				if (x[16] <= 0.5) {
					if (x[22] <= 0.5) {
						return 6.0f;
					}
					else {
						return 5.0f;
					}

				}
				else {
					if (x[12] <= 0.5) {
						return 0.0f;
					}
					else {
						return 5.0f;
					}

				}

			}

		}

	}

}