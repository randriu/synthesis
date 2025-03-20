#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f,0.f,0.f,0.f,1.f,1.f,0.f,0.f,2.f,2.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[11] <= 0.5) {
		if (x[12] <= 0.5) {
			if (x[1] <= 0.5) {
				if (x[0] <= 0.5) {
					if (x[7] <= 8.5) {
						if (x[3] <= 0.5) {
							return 2.0f;
						}
						else {
							if (x[5] <= 0.5) {
								if (x[7] <= 6.5) {
									return 10.0f;
								}
								else {
									if (x[8] <= 6.5) {
										return 10.0f;
									}
									else {
										return 3.0f;
									}

								}

							}
							else {
								return 2.0f;
							}

						}

					}
					else {
						if (x[8] <= 11.0) {
							return 3.0f;
						}
						else {
							return 2.0f;
						}

					}

				}
				else {
					if (x[7] <= 5.5) {
						return 3.0f;
					}
					else {
						if (x[7] <= 6.5) {
							return 16.0f;
						}
						else {
							return 3.0f;
						}

					}

				}

			}
			else {
				if (x[7] <= 9.0) {
					return 2.0f;
				}
				else {
					if (x[8] <= 6.5) {
						return 15.0f;
					}
					else {
						return 2.0f;
					}

				}

			}

		}
		else {
			if (x[8] <= 6.0) {
				if (x[7] <= 6.5) {
					if (x[0] <= 14.5) {
						if (x[7] <= 4.5) {
							return 8.0f;
						}
						else {
							return 9.0f;
						}

					}
					else {
						return 10.0f;
					}

				}
				else {
					if (x[1] <= 0.5) {
						return 1.0f;
					}
					else {
						return 14.0f;
					}

				}

			}
			else {
				if (x[5] <= 0.5) {
					if (x[1] <= 0.5) {
						return 3.0f;
					}
					else {
						return 17.0f;
					}

				}
				else {
					return 5.0f;
				}

			}

		}

	}
	else {
		if (x[0] <= 0.5) {
			if (x[4] <= 0.5) {
				if (x[2] <= 0.5) {
					if (x[6] <= 0.5) {
						return 0.0f;
					}
					else {
						if (x[7] <= 7.0) {
							return 7.0f;
						}
						else {
							return 6.0f;
						}

					}

				}
				else {
					if (x[7] <= 6.5) {
						if (x[1] <= 0.5) {
							if (x[8] <= 6.5) {
								return 12.0f;
							}
							else {
								return 13.0f;
							}

						}
						else {
							return 13.0f;
						}

					}
					else {
						if (x[8] <= 6.5) {
							return 12.0f;
						}
						else {
							return 2.0f;
						}

					}

				}

			}
			else {
				return 4.0f;
			}

		}
		else {
			if (x[7] <= 6.0) {
				return 11.0f;
			}
			else {
				return 18.0f;
			}

		}

	}

}