#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[12] <= 1.5) {
		if (x[9] <= 2.5) {
			if (x[9] <= 1.5) {
				if (x[0] <= 1.5) {
					if (x[4] <= 0.5) {
						if (x[0] <= 0.5) {
							return 0.0f;
						}
						else {
							return 1.0f;
						}

					}
					else {
						return 7.0f;
					}

				}
				else {
					if (x[9] <= 0.5) {
						return 2.0f;
					}
					else {
						return 3.0f;
					}

				}

			}
			else {
				if (x[0] <= 0.5) {
					if (x[8] <= 2.5) {
						if (x[5] <= 1.5) {
							if (x[7] <= 2.5) {
								return 4.0f;
							}
							else {
								return 5.0f;
							}

						}
						else {
							if (x[7] <= 2.5) {
								return 8.0f;
							}
							else {
								return 10.0f;
							}

						}

					}
					else {
						if (x[7] <= 2.5) {
							return 8.0f;
						}
						else {
							if (x[6] <= 1.5) {
								return 6.0f;
							}
							else {
								return 12.0f;
							}

						}

					}

				}
				else {
					return 12.0f;
				}

			}

		}
		else {
			if (x[9] <= 3.5) {
				return 7.0f;
			}
			else {
				if (x[6] <= 1.5) {
					return 17.0f;
				}
				else {
					if (x[8] <= 2.5) {
						if (x[7] <= 2.5) {
							if (x[7] <= 1.5) {
								if (x[0] <= 1.5) {
									return 10.0f;
								}
								else {
									return 3.0f;
								}

							}
							else {
								return 8.0f;
							}

						}
						else {
							if (x[11] <= 29.5) {
								if (x[10] <= 1.5) {
									if (x[0] <= 0.5) {
										return 10.0f;
									}
									else {
										return 7.0f;
									}

								}
								else {
									if (x[1] <= 0.5) {
										return 11.0f;
									}
									else {
										return 7.0f;
									}

								}

							}
							else {
								return 15.0f;
							}

						}

					}
					else {
						if (x[11] <= 1.5) {
							if (x[10] <= 29.5) {
								if (x[8] <= 3.5) {
									return 7.0f;
								}
								else {
									if (x[0] <= 0.5) {
										if (x[1] <= 0.5) {
											if (x[10] <= 1.5) {
												return 7.0f;
											}
											else {
												return 0.0f;
											}

										}
										else {
											return 7.0f;
										}

									}
									else {
										return 7.0f;
									}

								}

							}
							else {
								return 14.0f;
							}

						}
						else {
							if (x[2] <= 0.5) {
								if (x[13] <= 1.0) {
									if (x[1] <= 0.5) {
										if (x[10] <= 1.0) {
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
									if (x[10] <= 29.0) {
										return 9.0f;
									}
									else {
										return 14.0f;
									}

								}

							}
							else {
								if (x[10] <= 29.0) {
									if (x[0] <= 0.5) {
										if (x[1] <= 0.5) {
											if (x[7] <= 3.5) {
												return 0.0f;
											}
											else {
												return 7.0f;
											}

										}
										else {
											return 7.0f;
										}

									}
									else {
										return 7.0f;
									}

								}
								else {
									return 14.0f;
								}

							}

						}

					}

				}

			}

		}

	}
	else {
		if (x[8] <= 2.5) {
			if (x[8] <= 1.5) {
				if (x[3] <= 0.5) {
					if (x[7] <= 2.5) {
						if (x[0] <= 1.5) {
							return 8.0f;
						}
						else {
							return 2.0f;
						}

					}
					else {
						if (x[11] <= 1.0) {
							return 2.0f;
						}
						else {
							if (x[1] <= 0.5) {
								if (x[10] <= 1.0) {
									if (x[11] <= 29.0) {
										return 13.0f;
									}
									else {
										return 15.0f;
									}

								}
								else {
									if (x[11] <= 29.0) {
										return 11.0f;
									}
									else {
										return 15.0f;
									}

								}

							}
							else {
								if (x[11] <= 29.0) {
									return 13.0f;
								}
								else {
									return 15.0f;
								}

							}

						}

					}

				}
				else {
					if (x[7] <= 2.5) {
						if (x[0] <= 1.5) {
							return 8.0f;
						}
						else {
							return 3.0f;
						}

					}
					else {
						if (x[11] <= 29.0) {
							if (x[1] <= 0.5) {
								if (x[10] <= 1.0) {
									return 7.0f;
								}
								else {
									return 11.0f;
								}

							}
							else {
								return 7.0f;
							}

						}
						else {
							return 15.0f;
						}

					}

				}

			}
			else {
				if (x[0] <= 0.5) {
					if (x[7] <= 2.5) {
						return 8.0f;
					}
					else {
						return 10.0f;
					}

				}
				else {
					return 10.0f;
				}

			}

		}
		else {
			if (x[9] <= 2.0) {
				if (x[7] <= 2.5) {
					return 8.0f;
				}
				else {
					if (x[11] <= 1.5) {
						if (x[8] <= 3.5) {
							return 7.0f;
						}
						else {
							if (x[12] <= 29.5) {
								if (x[10] <= 1.5) {
									return 7.0f;
								}
								else {
									if (x[1] <= 0.5) {
										return 11.0f;
									}
									else {
										return 7.0f;
									}

								}

							}
							else {
								return 16.0f;
							}

						}

					}
					else {
						if (x[2] <= 0.5) {
							if (x[1] <= 0.5) {
								if (x[10] <= 1.0) {
									if (x[12] <= 29.0) {
										return 9.0f;
									}
									else {
										return 16.0f;
									}

								}
								else {
									if (x[12] <= 29.0) {
										return 11.0f;
									}
									else {
										return 16.0f;
									}

								}

							}
							else {
								if (x[12] <= 29.0) {
									return 9.0f;
								}
								else {
									return 16.0f;
								}

							}

						}
						else {
							if (x[12] <= 29.0) {
								if (x[1] <= 0.5) {
									if (x[10] <= 1.0) {
										return 7.0f;
									}
									else {
										return 11.0f;
									}

								}
								else {
									return 7.0f;
								}

							}
							else {
								return 16.0f;
							}

						}

					}

				}

			}
			else {
				if (x[3] <= 0.5) {
					if (x[13] <= 1.0) {
						if (x[2] <= 0.5) {
							if (x[8] <= 3.5) {
								if (x[1] <= 0.5) {
									if (x[10] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[4] <= 1.5) {
												return 17.0f;
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
									return 1.0f;
								}

							}
							else {
								if (x[5] <= 1.5) {
									return 17.0f;
								}
								else {
									if (x[1] <= 0.5) {
										if (x[10] <= 1.0) {
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
						else {
							if (x[1] <= 0.5) {
								if (x[10] <= 1.0) {
									if (x[0] <= 0.5) {
										if (x[4] <= 1.5) {
											return 17.0f;
										}
										else {
											return 2.0f;
										}

									}
									else {
										return 2.0f;
									}

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
					else {
						if (x[2] <= 0.5) {
							if (x[11] <= 1.0) {
								if (x[10] <= 29.0) {
									return 13.0f;
								}
								else {
									return 14.0f;
								}

							}
							else {
								if (x[10] <= 29.0) {
									return 9.0f;
								}
								else {
									return 14.0f;
								}

							}

						}
						else {
							if (x[10] <= 29.0) {
								return 13.0f;
							}
							else {
								return 14.0f;
							}

						}

					}

				}
				else {
					if (x[13] <= 1.0) {
						if (x[2] <= 0.5) {
							if (x[11] <= 1.0) {
								if (x[5] <= 1.5) {
									return 17.0f;
								}
								else {
									if (x[10] <= 1.0) {
										return 7.0f;
									}
									else {
										if (x[1] <= 0.5) {
											return 0.0f;
										}
										else {
											return 7.0f;
										}

									}

								}

							}
							else {
								if (x[1] <= 0.5) {
									if (x[10] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[4] <= 1.5) {
												return 17.0f;
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
									return 1.0f;
								}

							}

						}
						else {
							if (x[10] <= 1.0) {
								if (x[7] <= 3.5) {
									return 7.0f;
								}
								else {
									if (x[4] <= 1.5) {
										return 17.0f;
									}
									else {
										return 7.0f;
									}

								}

							}
							else {
								if (x[1] <= 0.5) {
									return 0.0f;
								}
								else {
									return 7.0f;
								}

							}

						}

					}
					else {
						if (x[10] <= 29.0) {
							if (x[2] <= 0.5) {
								if (x[11] <= 1.0) {
									return 7.0f;
								}
								else {
									return 9.0f;
								}

							}
							else {
								return 7.0f;
							}

						}
						else {
							return 14.0f;
						}

					}

				}

			}

		}

	}

}