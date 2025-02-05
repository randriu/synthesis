#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f,12.f,0.f,0.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[5] <= 1.5) {
		if (x[5] <= 0.5) {
			if (x[4] <= 10.5) {
				if (x[1] <= 0.5) {
					if (x[2] <= 0.5) {
						return 0.0f;
					}
					else {
						if (x[4] <= 9.5) {
							return 7.0f;
						}
						else {
							if (x[6] <= 1.0) {
								return 7.0f;
							}
							else {
								return 0.0f;
							}

						}

					}

				}
				else {
					return 6.0f;
				}

			}
			else {
				if (x[4] <= 13.5) {
					if (x[6] <= 1.5) {
						if (x[7] <= 1.5) {
							if (x[8] <= 1.0) {
								return 0.0f;
							}
							else {
								if (x[4] <= 11.5) {
									return 0.0f;
								}
								else {
									if (x[4] <= 12.5) {
										return 8.0f;
									}
									else {
										return 0.0f;
									}

								}

							}

						}
						else {
							if (x[4] <= 11.5) {
								return 0.0f;
							}
							else {
								if (x[4] <= 12.5) {
									return 5.0f;
								}
								else {
									return 0.0f;
								}

							}

						}

					}
					else {
						if (x[7] <= 1.5) {
							if (x[4] <= 11.5) {
								return 0.0f;
							}
							else {
								if (x[4] <= 12.5) {
									return 4.0f;
								}
								else {
									return 0.0f;
								}

							}

						}
						else {
							return 4.0f;
						}

					}

				}
				else {
					if (x[4] <= 15.5) {
						if (x[1] <= 0.5) {
							if (x[6] <= 1.5) {
								if (x[6] <= 0.5) {
									if (x[4] <= 14.5) {
										if (x[2] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 10.0f;
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
									else {
										return 0.0f;
									}

								}
								else {
									return 9.0f;
								}

							}
							else {
								if (x[4] <= 14.5) {
									return 0.0f;
								}
								else {
									if (x[2] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 10.0f;
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

						}
						else {
							return 0.0f;
						}

					}
					else {
						return 0.0f;
					}

				}

			}

		}
		else {
			if (x[0] <= 0.5) {
				if (x[4] <= 5.5) {
					if (x[6] <= 1.5) {
						if (x[7] <= 1.5) {
							if (x[8] <= 1.0) {
								return 1.0f;
							}
							else {
								return 8.0f;
							}

						}
						else {
							if (x[1] <= 0.5) {
								if (x[6] <= 0.5) {
									return 11.0f;
								}
								else {
									return 5.0f;
								}

							}
							else {
								return 6.0f;
							}

						}

					}
					else {
						return 4.0f;
					}

				}
				else {
					return 1.0f;
				}

			}
			else {
				if (x[4] <= 18.5) {
					return 2.0f;
				}
				else {
					if (x[6] <= 1.5) {
						if (x[7] <= 1.5) {
							if (x[8] <= 1.0) {
								return 2.0f;
							}
							else {
								return 8.0f;
							}

						}
						else {
							if (x[1] <= 0.5) {
								if (x[6] <= 0.5) {
									return 11.0f;
								}
								else {
									return 9.0f;
								}

							}
							else {
								return 5.0f;
							}

						}

					}
					else {
						return 4.0f;
					}

				}

			}

		}

	}
	else {
		if (x[5] <= 2.5) {
			if (x[4] <= 4.5) {
				if (x[8] <= 0.5) {
					if (x[1] <= 0.5) {
						if (x[6] <= 0.5) {
							return 11.0f;
						}
						else {
							if (x[2] <= 0.5) {
								if (x[7] <= 0.5) {
									return 12.0f;
								}
								else {
									return 13.0f;
								}

							}
							else {
								return 7.0f;
							}

						}

					}
					else {
						return 6.0f;
					}

				}
				else {
					if (x[3] <= 0.5) {
						return 14.0f;
					}
					else {
						return 15.0f;
					}

				}

			}
			else {
				if (x[4] <= 19.5) {
					return 3.0f;
				}
				else {
					if (x[1] <= 0.5) {
						if (x[6] <= 0.5) {
							return 11.0f;
						}
						else {
							return 9.0f;
						}

					}
					else {
						if (x[2] <= 0.5) {
							if (x[7] <= 0.5) {
								return 12.0f;
							}
							else {
								return 10.0f;
							}

						}
						else {
							if (x[3] <= 0.5) {
								if (x[8] <= 0.5) {
									return 13.0f;
								}
								else {
									return 16.0f;
								}

							}
							else {
								return 17.0f;
							}

						}

					}

				}

			}

		}
		else {
			if (x[7] <= 1.5) {
				if (x[0] <= 0.5) {
					if (x[4] <= 3.5) {
						if (x[6] <= 2.5) {
							return 18.0f;
						}
						else {
							return 10.0f;
						}

					}
					else {
						return 9.0f;
					}

				}
				else {
					if (x[1] <= 0.5) {
						return 19.0f;
					}
					else {
						if (x[4] <= 20.5) {
							return 6.0f;
						}
						else {
							return 7.0f;
						}

					}

				}

			}
			else {
				if (x[8] <= 1.5) {
					if (x[0] <= 0.5) {
						if (x[7] <= 2.5) {
							return 20.0f;
						}
						else {
							return 16.0f;
						}

					}
					else {
						if (x[2] <= 0.5) {
							return 21.0f;
						}
						else {
							return 15.0f;
						}

					}

				}
				else {
					if (x[8] <= 2.5) {
						if (x[0] <= 0.5) {
							return 22.0f;
						}
						else {
							return 23.0f;
						}

					}
					else {
						return 24.0f;
					}

				}

			}

		}

	}

}