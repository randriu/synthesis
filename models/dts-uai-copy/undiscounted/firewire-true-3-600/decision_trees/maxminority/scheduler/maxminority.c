#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[3] <= 0.5) {
		if (x[2] <= 425.5) {
			if (x[2] <= 258.5) {
				if (x[1] <= 1.5) {
					if (x[0] <= 3.0) {
						return 0.0f;
					}
					else {
						return 6.0f;
					}

				}
				else {
					if (x[2] <= 167.5) {
						if (x[2] <= 85.5) {
							if (x[1] <= 4.5) {
								if (x[2] <= 84.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}
							else {
								if (x[4] <= 0.5) {
									return 3.0f;
								}
								else {
									return 2.0f;
								}

							}

						}
						else {
							if (x[0] <= 4.5) {
								if (x[0] <= 2.5) {
									return 2.0f;
								}
								else {
									if (x[0] <= 3.5) {
										return 2.0f;
									}
									else {
										if (x[1] <= 4.5) {
											return 2.0f;
										}
										else {
											return 3.0f;
										}

									}

								}

							}
							else {
								if (x[5] <= 166.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}

						}

					}
					else {
						if (x[1] <= 4.5) {
							if (x[5] <= 84.5) {
								return 2.0f;
							}
							else {
								return 3.0f;
							}

						}
						else {
							if (x[0] <= 4.5) {
								if (x[0] <= 3.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}
							else {
								if (x[5] <= 166.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}

						}

					}

				}

			}
			else {
				if (x[2] <= 343.5) {
					if (x[2] <= 337.5) {
						if (x[0] <= 4.5) {
							if (x[0] <= 1.0) {
								return 0.0f;
							}
							else {
								if (x[1] <= 4.5) {
									if (x[5] <= 84.5) {
										return 2.0f;
									}
									else {
										return 3.0f;
									}

								}
								else {
									if (x[0] <= 3.5) {
										return 2.0f;
									}
									else {
										return 3.0f;
									}

								}

							}

						}
						else {
							if (x[0] <= 5.5) {
								if (x[5] <= 166.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}
							else {
								if (x[1] <= 1.5) {
									return 6.0f;
								}
								else {
									return 2.0f;
								}

							}

						}

					}
					else {
						if (x[0] <= 4.5) {
							if (x[0] <= 1.0) {
								return 0.0f;
							}
							else {
								if (x[1] <= 4.5) {
									if (x[5] <= 84.5) {
										return 2.0f;
									}
									else {
										return 3.0f;
									}

								}
								else {
									if (x[0] <= 3.5) {
										return 2.0f;
									}
									else {
										return 3.0f;
									}

								}

							}

						}
						else {
							if (x[0] <= 5.5) {
								if (x[5] <= 166.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}
							else {
								if (x[1] <= 1.5) {
									return 6.0f;
								}
								else {
									return 2.0f;
								}

							}

						}

					}

				}
				else {
					if (x[1] <= 1.5) {
						if (x[0] <= 3.0) {
							return 0.0f;
						}
						else {
							return 6.0f;
						}

					}
					else {
						if (x[1] <= 4.5) {
							if (x[5] <= 84.5) {
								return 2.0f;
							}
							else {
								return 3.0f;
							}

						}
						else {
							if (x[0] <= 4.5) {
								if (x[0] <= 3.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}
							else {
								if (x[5] <= 166.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}

						}

					}

				}

			}

		}
		else {
			if (x[2] <= 516.5) {
				if (x[1] <= 1.5) {
					if (x[0] <= 3.0) {
						return 0.0f;
					}
					else {
						return 6.0f;
					}

				}
				else {
					if (x[2] <= 504.5) {
						if (x[1] <= 4.5) {
							if (x[5] <= 84.5) {
								return 2.0f;
							}
							else {
								return 3.0f;
							}

						}
						else {
							if (x[0] <= 4.5) {
								if (x[0] <= 3.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}
							else {
								if (x[5] <= 166.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}

						}

					}
					else {
						if (x[0] <= 4.5) {
							if (x[1] <= 4.5) {
								if (x[5] <= 84.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}
							else {
								if (x[0] <= 3.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}

						}
						else {
							if (x[5] <= 166.5) {
								return 2.0f;
							}
							else {
								return 3.0f;
							}

						}

					}

				}

			}
			else {
				if (x[2] <= 592.5) {
					if (x[1] <= 1.5) {
						if (x[0] <= 3.0) {
							return 0.0f;
						}
						else {
							return 6.0f;
						}

					}
					else {
						if (x[1] <= 4.5) {
							if (x[5] <= 84.5) {
								return 2.0f;
							}
							else {
								return 3.0f;
							}

						}
						else {
							if (x[0] <= 4.5) {
								if (x[0] <= 3.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}
							else {
								if (x[5] <= 166.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}

						}

					}

				}
				else {
					if (x[2] <= 598.5) {
						if (x[0] <= 4.5) {
							if (x[0] <= 1.0) {
								return 0.0f;
							}
							else {
								if (x[1] <= 4.5) {
									if (x[5] <= 84.5) {
										return 2.0f;
									}
									else {
										return 3.0f;
									}

								}
								else {
									if (x[0] <= 3.5) {
										return 2.0f;
									}
									else {
										return 3.0f;
									}

								}

							}

						}
						else {
							if (x[0] <= 5.5) {
								if (x[5] <= 166.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}
							else {
								if (x[1] <= 1.5) {
									return 6.0f;
								}
								else {
									return 2.0f;
								}

							}

						}

					}
					else {
						if (x[0] <= 4.5) {
							if (x[0] <= 1.0) {
								return 0.0f;
							}
							else {
								if (x[1] <= 4.5) {
									if (x[5] <= 84.5) {
										return 2.0f;
									}
									else {
										return 3.0f;
									}

								}
								else {
									if (x[0] <= 3.5) {
										return 2.0f;
									}
									else {
										return 3.0f;
									}

								}

							}

						}
						else {
							if (x[0] <= 5.5) {
								if (x[5] <= 166.5) {
									return 2.0f;
								}
								else {
									return 3.0f;
								}

							}
							else {
								if (x[1] <= 1.5) {
									return 6.0f;
								}
								else {
									return 2.0f;
								}

							}

						}

					}

				}

			}

		}

	}
	else {
		if (x[1] <= 4.5) {
			if (x[0] <= 4.5) {
				return 1.0f;
			}
			else {
				return 4.0f;
			}

		}
		else {
			if (x[7] <= 2.5) {
				if (x[6] <= 122.5) {
					return 2.0f;
				}
				else {
					return 4.0f;
				}

			}
			else {
				return 5.0f;
			}

		}

	}

}