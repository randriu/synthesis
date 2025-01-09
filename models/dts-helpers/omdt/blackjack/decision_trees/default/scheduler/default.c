#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[2] <= 0.5) {
		if (x[1] <= 11.5) {
			if (x[0] <= 1.0) {
				return 0.0f;
			}
			else {
				return 1.0f;
			}

		}
		else {
			if (x[1] <= 14.5) {
				if (x[0] <= 6.5) {
					return 0.0f;
				}
				else {
					if (x[0] <= 10.5) {
						if (x[0] <= 9.5) {
							return 1.0f;
						}
						else {
							if (x[1] <= 13.5) {
								return 1.0f;
							}
							else {
								return 0.0f;
							}

						}

					}
					else {
						return 0.0f;
					}

				}

			}
			else {
				return 0.0f;
			}

		}

	}
	else {
		return 0.0f;
	}

}