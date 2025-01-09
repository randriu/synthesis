#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[3] <= 1.5) {
		if (x[2] <= 0.5) {
			if (x[0] <= 1.5) {
				if (x[1] <= 0.5) {
					return 0.0f;
				}
				else {
					return 1.0f;
				}

			}
			else {
				return 0.0f;
			}

		}
		else {
			if (x[0] <= 2.5) {
				if (x[0] <= 1.5) {
					return 0.0f;
				}
				else {
					if (x[1] <= 1.5) {
						return 1.0f;
					}
					else {
						return 0.0f;
					}

				}

			}
			else {
				if (x[0] <= 4.5) {
					if (x[1] <= 1.5) {
						return 1.0f;
					}
					else {
						if (x[1] <= 2.5) {
							return 0.0f;
						}
						else {
							if (x[1] <= 4.5) {
								return 1.0f;
							}
							else {
								if (x[0] <= 3.5) {
									return 0.0f;
								}
								else {
									return 1.0f;
								}

							}

						}

					}

				}
				else {
					return 1.0f;
				}

			}

		}

	}
	else {
		if (x[0] <= 0.5) {
			if (x[2] <= 0.5) {
				if (x[1] <= 0.5) {
					if (x[3] <= 2.5) {
						return 0.0f;
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
				return 0.0f;
			}

		}
		else {
			if (x[2] <= 0.5) {
				if (x[1] <= 0.5) {
					if (x[0] <= 1.5) {
						if (x[3] <= 2.5) {
							return 0.0f;
						}
						else {
							return 1.0f;
						}

					}
					else {
						return 0.0f;
					}

				}
				else {
					if (x[3] <= 2.5) {
						if (x[0] <= 1.5) {
							return 1.0f;
						}
						else {
							if (x[0] <= 2.5) {
								return 0.0f;
							}
							else {
								if (x[1] <= 3.5) {
									if (x[1] <= 1.5) {
										return 0.0f;
									}
									else {
										if (x[0] <= 3.5) {
											return 1.0f;
										}
										else {
											if (x[0] <= 4.5) {
												return 0.0f;
											}
											else {
												if (x[1] <= 2.5) {
													return 0.0f;
												}
												else {
													return 1.0f;
												}

											}

										}

									}

								}
								else {
									return 1.0f;
								}

							}

						}

					}
					else {
						if (x[1] <= 1.5) {
							if (x[3] <= 3.5) {
								if (x[0] <= 2.5) {
									if (x[0] <= 1.5) {
										return 1.0f;
									}
									else {
										return 0.0f;
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

}