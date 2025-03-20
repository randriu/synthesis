#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,99.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[3] <= 1.5) {
		if (x[0] <= 0.5) {
			if (x[3] <= 0.5) {
				if (x[4] <= 1.5) {
					if (x[1] <= 0.5) {
						if (x[2] <= 100.5) {
							return 0.0f;
						}
						else {
							if (x[4] <= 0.5) {
								return 0.0f;
							}
							else {
								return 6.0f;
							}

						}

					}
					else {
						if (x[2] <= 97.5) {
							return 5.0f;
						}
						else {
							return 0.0f;
						}

					}

				}
				else {
					if (x[4] <= 2.5) {
						if (x[2] <= 98.5) {
							return 0.0f;
						}
						else {
							if (x[2] <= 99.5) {
								return 4.0f;
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
				if (x[1] <= 0.5) {
					if (x[2] <= 4.5) {
						if (x[4] <= 1.5) {
							if (x[4] <= 0.5) {
								return 1.0f;
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
						if (x[2] <= 99.5) {
							if (x[2] <= 98.5) {
								return 1.0f;
							}
							else {
								if (x[4] <= 1.5) {
									return 1.0f;
								}
								else {
									if (x[4] <= 2.5) {
										return 4.0f;
									}
									else {
										return 1.0f;
									}

								}

							}

						}
						else {
							return 1.0f;
						}

					}

				}
				else {
					if (x[2] <= 97.5) {
						if (x[4] <= 2.0) {
							return 5.0f;
						}
						else {
							return 1.0f;
						}

					}
					else {
						return 1.0f;
					}

				}

			}

		}
		else {
			if (x[2] <= 100.5) {
				if (x[2] <= 98.5) {
					return 2.0f;
				}
				else {
					if (x[2] <= 99.5) {
						if (x[4] <= 1.5) {
							return 2.0f;
						}
						else {
							if (x[4] <= 2.5) {
								return 4.0f;
							}
							else {
								return 2.0f;
							}

						}

					}
					else {
						return 2.0f;
					}

				}

			}
			else {
				if (x[4] <= 1.5) {
					if (x[1] <= 0.5) {
						if (x[4] <= 0.5) {
							return 2.0f;
						}
						else {
							return 6.0f;
						}

					}
					else {
						return 2.0f;
					}

				}
				else {
					if (x[2] <= 193.5) {
						return 2.0f;
					}
					else {
						if (x[4] <= 2.5) {
							if (x[2] <= 194.5) {
								return 4.0f;
							}
							else {
								return 2.0f;
							}

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
		if (x[3] <= 2.5) {
			if (x[4] <= 1.5) {
				if (x[1] <= 0.5) {
					if (x[4] <= 0.5) {
						if (x[2] <= 4.5) {
							return 7.0f;
						}
						else {
							if (x[2] <= 194.5) {
								return 3.0f;
							}
							else {
								return 7.0f;
							}

						}

					}
					else {
						if (x[2] <= 101.5) {
							if (x[2] <= 4.5) {
								return 6.0f;
							}
							else {
								return 3.0f;
							}

						}
						else {
							return 6.0f;
						}

					}

				}
				else {
					if (x[2] <= 96.5) {
						return 5.0f;
					}
					else {
						if (x[2] <= 194.5) {
							return 3.0f;
						}
						else {
							return 9.0f;
						}

					}

				}

			}
			else {
				if (x[2] <= 3.5) {
					return 8.0f;
				}
				else {
					if (x[2] <= 194.5) {
						return 3.0f;
					}
					else {
						return 9.0f;
					}

				}

			}

		}
		else {
			if (x[4] <= 1.5) {
				if (x[1] <= 0.5) {
					if (x[4] <= 0.5) {
						return 7.0f;
					}
					else {
						return 6.0f;
					}

				}
				else {
					return 5.0f;
				}

			}
			else {
				if (x[2] <= 194.5) {
					if (x[2] <= 3.5) {
						if (x[4] <= 2.5) {
							return 10.0f;
						}
						else {
							return 12.0f;
						}

					}
					else {
						return 4.0f;
					}

				}
				else {
					if (x[4] <= 2.5) {
						return 11.0f;
					}
					else {
						return 12.0f;
					}

				}

			}

		}

	}

}