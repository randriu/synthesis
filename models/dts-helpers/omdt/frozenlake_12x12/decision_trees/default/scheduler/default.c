#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[1] <= 1.5) {
		if (x[0] <= 8.5) {
			if (x[0] <= 0.5) {
				return 0.0f;
			}
			else {
				if (x[1] <= 0.5) {
					return 1.0f;
				}
				else {
					if (x[0] <= 4.5) {
						return 3.0f;
					}
					else {
						if (x[0] <= 7.5) {
							return 1.0f;
						}
						else {
							return 0.0f;
						}

					}

				}

			}

		}
		else {
			if (x[1] <= 0.5) {
				return 2.0f;
			}
			else {
				if (x[0] <= 9.5) {
					return 0.0f;
				}
				else {
					if (x[0] <= 10.5) {
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
		if (x[1] <= 10.5) {
			if (x[1] <= 9.5) {
				if (x[0] <= 5.5) {
					if (x[1] <= 6.5) {
						if (x[0] <= 3.5) {
							if (x[0] <= 1.5) {
								if (x[0] <= 0.5) {
									return 2.0f;
								}
								else {
									if (x[1] <= 3.5) {
										return 2.0f;
									}
									else {
										if (x[1] <= 4.5) {
											return 3.0f;
										}
										else {
											return 2.0f;
										}

									}

								}

							}
							else {
								if (x[1] <= 2.5) {
									return 2.0f;
								}
								else {
									if (x[0] <= 2.5) {
										if (x[1] <= 5.5) {
											return 2.0f;
										}
										else {
											return 0.0f;
										}

									}
									else {
										if (x[1] <= 3.5) {
											return 0.0f;
										}
										else {
											if (x[1] <= 4.5) {
												return 2.0f;
											}
											else {
												if (x[1] <= 5.5) {
													return 0.0f;
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
						else {
							if (x[1] <= 2.5) {
								if (x[0] <= 4.5) {
									return 1.0f;
								}
								else {
									return 3.0f;
								}

							}
							else {
								if (x[0] <= 4.5) {
									if (x[1] <= 4.5) {
										if (x[1] <= 3.5) {
											return 2.0f;
										}
										else {
											return 1.0f;
										}

									}
									else {
										if (x[1] <= 5.5) {
											return 3.0f;
										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[1] <= 4.5) {
										if (x[1] <= 3.5) {
											return 2.0f;
										}
										else {
											return 0.0f;
										}

									}
									else {
										return 2.0f;
									}

								}

							}

						}

					}
					else {
						if (x[1] <= 8.5) {
							if (x[1] <= 7.5) {
								if (x[0] <= 1.5) {
									return 0.0f;
								}
								else {
									if (x[0] <= 3.5) {
										return 2.0f;
									}
									else {
										return 0.0f;
									}

								}

							}
							else {
								if (x[0] <= 0.5) {
									return 3.0f;
								}
								else {
									if (x[0] <= 4.5) {
										return 0.0f;
									}
									else {
										return 3.0f;
									}

								}

							}

						}
						else {
							if (x[0] <= 1.5) {
								if (x[0] <= 0.5) {
									return 2.0f;
								}
								else {
									return 1.0f;
								}

							}
							else {
								if (x[0] <= 3.5) {
									return 0.0f;
								}
								else {
									return 2.0f;
								}

							}

						}

					}

				}
				else {
					if (x[0] <= 7.5) {
						if (x[1] <= 6.5) {
							if (x[0] <= 6.5) {
								if (x[1] <= 3.5) {
									return 1.0f;
								}
								else {
									if (x[1] <= 4.5) {
										return 3.0f;
									}
									else {
										return 2.0f;
									}

								}

							}
							else {
								return 1.0f;
							}

						}
						else {
							if (x[1] <= 8.5) {
								if (x[0] <= 6.5) {
									return 0.0f;
								}
								else {
									if (x[1] <= 7.5) {
										return 0.0f;
									}
									else {
										return 2.0f;
									}

								}

							}
							else {
								if (x[0] <= 6.5) {
									return 1.0f;
								}
								else {
									return 0.0f;
								}

							}

						}

					}
					else {
						if (x[1] <= 7.5) {
							if (x[0] <= 9.5) {
								if (x[1] <= 3.5) {
									return 0.0f;
								}
								else {
									if (x[1] <= 5.5) {
										if (x[1] <= 4.5) {
											if (x[0] <= 8.5) {
												return 0.0f;
											}
											else {
												return 3.0f;
											}

										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[0] <= 8.5) {
											if (x[1] <= 6.5) {
												return 0.0f;
											}
											else {
												return 3.0f;
											}

										}
										else {
											return 0.0f;
										}

									}

								}

							}
							else {
								if (x[1] <= 2.5) {
									return 2.0f;
								}
								else {
									if (x[1] <= 6.5) {
										if (x[0] <= 10.5) {
											if (x[1] <= 4.5) {
												return 0.0f;
											}
											else {
												if (x[1] <= 5.5) {
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
									else {
										if (x[0] <= 10.5) {
											return 2.0f;
										}
										else {
											return 0.0f;
										}

									}

								}

							}

						}
						else {
							if (x[1] <= 8.5) {
								if (x[0] <= 9.5) {
									if (x[0] <= 8.5) {
										return 2.0f;
									}
									else {
										return 1.0f;
									}

								}
								else {
									return 3.0f;
								}

							}
							else {
								if (x[0] <= 8.5) {
									return 0.0f;
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
				if (x[0] <= 5.5) {
					return 0.0f;
				}
				else {
					if (x[0] <= 6.5) {
						return 2.0f;
					}
					else {
						return 0.0f;
					}

				}

			}

		}
		else {
			if (x[0] <= 6.5) {
				if (x[0] <= 0.5) {
					return 0.0f;
				}
				else {
					return 1.0f;
				}

			}
			else {
				if (x[0] <= 10.5) {
					return 2.0f;
				}
				else {
					return 0.0f;
				}

			}

		}

	}

}