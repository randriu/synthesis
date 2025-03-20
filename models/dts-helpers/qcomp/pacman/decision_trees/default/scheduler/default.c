#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {1.f,1.f,0.f,2.f,2.f,5.f,5.f,3.f,5.f,5.f,1.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[6] <= 1.0) {
		return 2.0f;
	}
	else {
		if (x[0] <= 1.5) {
			return 0.0f;
		}
		else {
			if (x[0] <= 2.5) {
				return 1.0f;
			}
			else {
				return 0.0f;
			}

		}

	}

}