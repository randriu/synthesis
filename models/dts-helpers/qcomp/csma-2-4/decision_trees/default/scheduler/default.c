#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[7] <= 29.5) {
		if (x[8] <= 29.5) {
			if (x[5] <= 2.5) {
				if (x[6] <= 2.5) {
					if (x[5] <= 1.5) {
						if (x[4] <= 3.5) {
							if (x[6] <= 1.5) {
								if (x[0] <= 1.5) {
									if (x[5] <= 0.5) {
										return 0.0f;
									}
									else {
										return 1.0f;
									}

								}
								else {
									return 2.0f;
								}

							}
							else {
								if (x[4] <= 2.5) {
									return 9.0f;
								}
								else {
									return 10.0f;
								}

							}

						}
						else {
							if (x[0] <= 1.5) {
								return 12.0f;
							}
							else {
								return 2.0f;
							}

						}

					}
					else {
						if (x[3] <= 3.5) {
							if (x[3] <= 2.5) {
								if (x[3] <= 1.5) {
									return 3.0f;
								}
								else {
									return 6.0f;
								}

							}
							else {
								return 11.0f;
							}

						}
						else {
							return 13.0f;
						}

					}

				}
				else {
					if (x[2] <= 0.5) {
						if (x[8] <= 1.5) {
							if (x[0] <= 0.5) {
								if (x[3] <= 3.5) {
									if (x[3] <= 1.5) {
										return 3.0f;
									}
									else {
										if (x[3] <= 2.5) {
											return 6.0f;
										}
										else {
											return 11.0f;
										}

									}

								}
								else {
									return 13.0f;
								}

							}
							else {
								return 5.0f;
							}

						}
						else {
							if (x[7] <= 1.0) {
								return 1.0f;
							}
							else {
								return 7.0f;
							}

						}

					}
					else {
						if (x[0] <= 0.5) {
							if (x[3] <= 3.5) {
								if (x[3] <= 2.5) {
									if (x[3] <= 1.5) {
										return 3.0f;
									}
									else {
										return 6.0f;
									}

								}
								else {
									return 11.0f;
								}

							}
							else {
								return 13.0f;
							}

						}
						else {
							return 5.0f;
						}

					}

				}

			}
			else {
				if (x[1] <= 0.5) {
					if (x[7] <= 1.5) {
						if (x[8] <= 0.5) {
							if (x[6] <= 2.5) {
								if (x[0] <= 0.5) {
									if (x[4] <= 3.5) {
										if (x[3] <= 1.5) {
											return 4.0f;
										}
										else {
											if (x[3] <= 2.5) {
												return 9.0f;
											}
											else {
												return 10.0f;
											}

										}

									}
									else {
										return 12.0f;
									}

								}
								else {
									return 5.0f;
								}

							}
							else {
								return 5.0f;
							}

						}
						else {
							if (x[0] <= 0.5) {
								if (x[2] <= 0.5) {
									if (x[8] <= 1.5) {
										return 5.0f;
									}
									else {
										return 1.0f;
									}

								}
								else {
									return 5.0f;
								}

							}
							else {
								return 5.0f;
							}

						}

					}
					else {
						if (x[9] <= 1.0) {
							return 0.0f;
						}
						else {
							return 8.0f;
						}

					}

				}
				else {
					if (x[0] <= 0.5) {
						if (x[6] <= 2.5) {
							if (x[3] <= 3.5) {
								if (x[3] <= 2.5) {
									if (x[3] <= 1.5) {
										return 4.0f;
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
								return 12.0f;
							}

						}
						else {
							if (x[2] <= 0.5) {
								if (x[8] <= 1.5) {
									return 5.0f;
								}
								else {
									return 1.0f;
								}

							}
							else {
								return 5.0f;
							}

						}

					}
					else {
						return 5.0f;
					}

				}

			}

		}
		else {
			if (x[5] <= 2.5) {
				return 13.0f;
			}
			else {
				return 15.0f;
			}

		}

	}
	else {
		if (x[6] <= 2.5) {
			return 12.0f;
		}
		else {
			return 14.0f;
		}

	}

}