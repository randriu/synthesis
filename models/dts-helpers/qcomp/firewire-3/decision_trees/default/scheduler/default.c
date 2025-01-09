#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[2] <= 0.5) {
		if (x[3] <= 0.5) {
			if (x[4] <= 75.5) {
				if (x[1] <= 3.5) {
					if (x[0] <= 4.5) {
						if (x[0] <= 1.5) {
							return 0.0f;
						}
						else {
							return 2.0f;
						}

					}
					else {
						if (x[5] <= 158.5) {
							if (x[1] <= 2.5) {
								if (x[5] <= 75.5) {
									return 3.0f;
								}
								else {
									return 8.0f;
								}

							}
							else {
								return 3.0f;
							}

						}
						else {
							return 8.0f;
						}

					}

				}
				else {
					return 3.0f;
				}

			}
			else {
				if (x[0] <= 4.5) {
					if (x[0] <= 3.5) {
						if (x[0] <= 2.5) {
							return 9.0f;
						}
						else {
							if (x[4] <= 158.5) {
								return 3.0f;
							}
							else {
								return 9.0f;
							}

						}

					}
					else {
						return 5.0f;
					}

				}
				else {
					if (x[4] <= 158.5) {
						if (x[1] <= 4.5) {
							if (x[5] <= 84.5) {
								return 3.0f;
							}
							else {
								return 12.0f;
							}

						}
						else {
							return 3.0f;
						}

					}
					else {
						return 5.0f;
					}

				}

			}

		}
		else {
			if (x[0] <= 3.5) {
				if (x[5] <= 2.5) {
					if (x[0] <= 1.0) {
						return 0.0f;
					}
					else {
						return 3.0f;
					}

				}
				else {
					if (x[0] <= 1.0) {
						return 0.0f;
					}
					else {
						return 4.0f;
					}

				}

			}
			else {
				if (x[8] <= 2.5) {
					if (x[4] <= 158.5) {
						if (x[0] <= 4.5) {
							if (x[4] <= 75.5) {
								return 3.0f;
							}
							else {
								return 7.0f;
							}

						}
						else {
							if (x[0] <= 5.5) {
								return 3.0f;
							}
							else {
								if (x[1] <= 5.0) {
									return 7.0f;
								}
								else {
									return 10.0f;
								}

							}

						}

					}
					else {
						return 7.0f;
					}

				}
				else {
					if (x[1] <= 6.5) {
						return 7.0f;
					}
					else {
						return 10.0f;
					}

				}

			}

		}

	}
	else {
		if (x[1] <= 3.5) {
			if (x[4] <= 2.5) {
				if (x[9] <= 2.5) {
					if (x[1] <= 1.0) {
						return 1.0f;
					}
					else {
						return 3.0f;
					}

				}
				else {
					return 1.0f;
				}

			}
			else {
				return 1.0f;
			}

		}
		else {
			if (x[1] <= 5.5) {
				if (x[5] <= 158.5) {
					if (x[1] <= 4.5) {
						if (x[5] <= 75.5) {
							return 3.0f;
						}
						else {
							return 6.0f;
						}

					}
					else {
						if (x[6] <= 2.5) {
							return 3.0f;
						}
						else {
							return 6.0f;
						}

					}

				}
				else {
					return 6.0f;
				}

			}
			else {
				if (x[0] <= 1.0) {
					return 0.0f;
				}
				else {
					if (x[0] <= 6.5) {
						return 6.0f;
					}
					else {
						return 11.0f;
					}

				}

			}

		}

	}

}