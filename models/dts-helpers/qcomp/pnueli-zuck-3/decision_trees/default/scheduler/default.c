#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {1.f,1.f,1.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[0] <= 5.5) {
		if (x[0] <= 2.5) {
			if (x[2] <= 8.5) {
				if (x[2] <= 1.5) {
					if (x[1] <= 5.5) {
						if (x[0] <= 0.5) {
							if (x[1] <= 2.5) {
								return 17.0f;
							}
							else {
								return 34.0f;
							}

						}
						else {
							return 0.0f;
						}

					}
					else {
						if (x[1] <= 7.5) {
							return 33.0f;
						}
						else {
							if (x[1] <= 8.5) {
								return 35.0f;
							}
							else {
								return 36.0f;
							}

						}

					}

				}
				else {
					if (x[2] <= 5.5) {
						if (x[2] <= 3.0) {
							if (x[0] <= 1.5) {
								return 1.0f;
							}
							else {
								return 2.0f;
							}

						}
						else {
							return 5.0f;
						}

					}
					else {
						if (x[2] <= 7.5) {
							if (x[0] <= 0.5) {
								return 17.0f;
							}
							else {
								if (x[0] <= 1.5) {
									return 1.0f;
								}
								else {
									return 6.0f;
								}

							}

						}
						else {
							return 9.0f;
						}

					}

				}

			}
			else {
				if (x[2] <= 12.0) {
					if (x[2] <= 9.5) {
						return 12.0f;
					}
					else {
						if (x[2] <= 10.5) {
							return 8.0f;
						}
						else {
							return 11.0f;
						}

					}

				}
				else {
					if (x[2] <= 13.5) {
						return 14.0f;
					}
					else {
						if (x[0] <= 0.5) {
							if (x[1] <= 1.5) {
								if (x[2] <= 14.5) {
									return 24.0f;
								}
								else {
									return 31.0f;
								}

							}
							else {
								return 17.0f;
							}

						}
						else {
							if (x[0] <= 1.5) {
								return 1.0f;
							}
							else {
								return 2.0f;
							}

						}

					}

				}

			}

		}
		else {
			if (x[0] <= 3.5) {
				if (x[1] <= 1.5) {
					if (x[2] <= 2.5) {
						return 3.0f;
					}
					else {
						return 4.0f;
					}

				}
				else {
					return 25.0f;
				}

			}
			else {
				if (x[2] <= 8.5) {
					if (x[0] <= 4.5) {
						return 7.0f;
					}
					else {
						return 23.0f;
					}

				}
				else {
					if (x[2] <= 14.5) {
						if (x[0] <= 4.5) {
							return 20.0f;
						}
						else {
							return 24.0f;
						}

					}
					else {
						return 28.0f;
					}

				}

			}

		}

	}
	else {
		if (x[0] <= 12.0) {
			if (x[0] <= 8.5) {
				if (x[0] <= 7.5) {
					if (x[0] <= 6.5) {
						return 26.0f;
					}
					else {
						return 19.0f;
					}

				}
				else {
					return 22.0f;
				}

			}
			else {
				if (x[0] <= 9.5) {
					if (x[1] <= 1.5) {
						return 27.0f;
					}
					else {
						if (x[1] <= 2.5) {
							return 29.0f;
						}
						else {
							return 27.0f;
						}

					}

				}
				else {
					if (x[0] <= 10.5) {
						return 10.0f;
					}
					else {
						return 13.0f;
					}

				}

			}

		}
		else {
			if (x[0] <= 13.5) {
				if (x[1] <= 2.0) {
					if (x[2] <= 5.0) {
						if (x[2] <= 1.5) {
							return 18.0f;
						}
						else {
							return 16.0f;
						}

					}
					else {
						if (x[2] <= 7.5) {
							return 6.0f;
						}
						else {
							return 18.0f;
						}

					}

				}
				else {
					if (x[1] <= 5.0) {
						return 30.0f;
					}
					else {
						if (x[1] <= 7.5) {
							return 33.0f;
						}
						else {
							return 18.0f;
						}

					}

				}

			}
			else {
				if (x[0] <= 14.5) {
					return 21.0f;
				}
				else {
					if (x[2] <= 0.5) {
						if (x[1] <= 4.5) {
							return 32.0f;
						}
						else {
							return 15.0f;
						}

					}
					else {
						return 15.0f;
					}

				}

			}

		}

	}

}