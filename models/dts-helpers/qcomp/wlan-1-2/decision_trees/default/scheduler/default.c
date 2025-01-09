#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f,0.f,0.f,0.f,1.f,1.f,0.f,0.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[11] <= 0.5) {
		if (x[8] <= 5.5) {
			if (x[12] <= 0.5) {
				if (x[7] <= 6.5) {
					if (x[7] <= 4.5) {
						if (x[2] <= 0.5) {
							return 0.0f;
						}
						else {
							return 13.0f;
						}

					}
					else {
						if (x[8] <= 4.5) {
							if (x[3] <= 0.5) {
								return 0.0f;
							}
							else {
								return 15.0f;
							}

						}
						else {
							return 0.0f;
						}

					}

				}
				else {
					if (x[7] <= 10.5) {
						if (x[4] <= 0.5) {
							if (x[8] <= 2.5) {
								return 7.0f;
							}
							else {
								if (x[1] <= 0.5) {
									if (x[3] <= 0.5) {
										return 3.0f;
									}
									else {
										if (x[8] <= 4.5) {
											return 15.0f;
										}
										else {
											return 0.0f;
										}

									}

								}
								else {
									return 3.0f;
								}

							}

						}
						else {
							if (x[8] <= 4.5) {
								if (x[8] <= 2.5) {
									return 0.0f;
								}
								else {
									if (x[3] <= 0.5) {
										return 11.0f;
									}
									else {
										return 15.0f;
									}

								}

							}
							else {
								return 23.0f;
							}

						}

					}
					else {
						if (x[8] <= 2.5) {
							return 7.0f;
						}
						else {
							if (x[8] <= 4.5) {
								if (x[3] <= 0.5) {
									return 0.0f;
								}
								else {
									return 15.0f;
								}

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
					if (x[12] <= 1.5) {
						if (x[3] <= 0.5) {
							if (x[4] <= 0.5) {
								if (x[7] <= 6.5) {
									return 0.0f;
								}
								else {
									if (x[2] <= 0.5) {
										return 0.0f;
									}
									else {
										return 3.0f;
									}

								}

							}
							else {
								return 11.0f;
							}

						}
						else {
							if (x[7] <= 4.5) {
								if (x[2] <= 0.5) {
									return 21.0f;
								}
								else {
									return 13.0f;
								}

							}
							else {
								return 21.0f;
							}

						}

					}
					else {
						if (x[8] <= 2.0) {
							return 2.0f;
						}
						else {
							if (x[4] <= 0.5) {
								if (x[7] <= 4.5) {
									return 13.0f;
								}
								else {
									if (x[0] <= 14.5) {
										return 16.0f;
									}
									else {
										if (x[12] <= 2.5) {
											return 0.0f;
										}
										else {
											return 16.0f;
										}

									}

								}

							}
							else {
								return 11.0f;
							}

						}

					}

				}
				else {
					if (x[7] <= 4.5) {
						if (x[2] <= 0.5) {
							return 22.0f;
						}
						else {
							return 13.0f;
						}

					}
					else {
						return 22.0f;
					}

				}

			}

		}
		else {
			if (x[12] <= 2.5) {
				if (x[8] <= 7.5) {
					if (x[4] <= 0.5) {
						if (x[8] <= 6.5) {
							return 25.0f;
						}
						else {
							if (x[2] <= 0.5) {
								if (x[12] <= 1.5) {
									return 0.0f;
								}
								else {
									return 29.0f;
								}

							}
							else {
								return 3.0f;
							}

						}

					}
					else {
						if (x[8] <= 6.5) {
							return 0.0f;
						}
						else {
							return 27.0f;
						}

					}

				}
				else {
					if (x[5] <= 0.5) {
						if (x[8] <= 10.5) {
							if (x[8] <= 9.0) {
								if (x[3] <= 0.5) {
									if (x[4] <= 0.5) {
										return 3.0f;
									}
									else {
										return 4.0f;
									}

								}
								else {
									if (x[7] <= 4.5) {
										if (x[2] <= 0.5) {
											return 4.0f;
										}
										else {
											return 13.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 6.5) {
												if (x[12] <= 0.5) {
													return 0.0f;
												}
												else {
													return 4.0f;
												}

											}
											else {
												return 4.0f;
											}

										}
										else {
											return 4.0f;
										}

									}

								}

							}
							else {
								if (x[7] <= 6.5) {
									if (x[2] <= 0.5) {
										if (x[7] <= 2.5) {
											return 8.0f;
										}
										else {
											return 4.0f;
										}

									}
									else {
										return 26.0f;
									}

								}
								else {
									return 4.0f;
								}

							}

						}
						else {
							if (x[7] <= 5.5) {
								if (x[7] <= 4.5) {
									if (x[2] <= 0.5) {
										if (x[7] <= 2.5) {
											return 8.0f;
										}
										else {
											return 0.0f;
										}

									}
									else {
										return 13.0f;
									}

								}
								else {
									return 0.0f;
								}

							}
							else {
								if (x[7] <= 6.5) {
									return 26.0f;
								}
								else {
									if (x[7] <= 7.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 8.5) {
											return 3.0f;
										}
										else {
											if (x[4] <= 0.5) {
												if (x[2] <= 0.5) {
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

							}

						}

					}
					else {
						if (x[7] <= 5.5) {
							if (x[2] <= 0.5) {
								if (x[7] <= 2.5) {
									return 0.0f;
								}
								else {
									return 12.0f;
								}

							}
							else {
								if (x[7] <= 4.5) {
									return 13.0f;
								}
								else {
									return 24.0f;
								}

							}

						}
						else {
							if (x[7] <= 6.5) {
								return 0.0f;
							}
							else {
								if (x[7] <= 7.5) {
									return 28.0f;
								}
								else {
									if (x[7] <= 8.5) {
										return 3.0f;
									}
									else {
										return 0.0f;
									}

								}

							}

						}

					}

				}

			}
			else {
				if (x[5] <= 0.5) {
					if (x[3] <= 0.5) {
						if (x[12] <= 5.5) {
							if (x[7] <= 6.5) {
								if (x[7] <= 4.5) {
									return 13.0f;
								}
								else {
									return 0.0f;
								}

							}
							else {
								if (x[4] <= 0.5) {
									return 3.0f;
								}
								else {
									return 0.0f;
								}

							}

						}
						else {
							return 20.0f;
						}

					}
					else {
						return 29.0f;
					}

				}
				else {
					if (x[12] <= 3.5) {
						if (x[8] <= 9.5) {
							if (x[5] <= 1.5) {
								if (x[7] <= 4.5) {
									if (x[7] <= 2.5) {
										return 0.0f;
									}
									else {
										return 12.0f;
									}

								}
								else {
									return 0.0f;
								}

							}
							else {
								if (x[7] <= 6.5) {
									return 0.0f;
								}
								else {
									return 9.0f;
								}

							}

						}
						else {
							return 6.0f;
						}

					}
					else {
						return 6.0f;
					}

				}

			}

		}

	}
	else {
		if (x[0] <= 0.5) {
			if (x[4] <= 0.5) {
				if (x[7] <= 7.5) {
					if (x[11] <= 1.5) {
						if (x[2] <= 0.5) {
							if (x[12] <= 0.5) {
								if (x[5] <= 0.5) {
									if (x[8] <= 6.5) {
										return 0.0f;
									}
									else {
										if (x[3] <= 0.5) {
											return 0.0f;
										}
										else {
											return 4.0f;
										}

									}

								}
								else {
									return 12.0f;
								}

							}
							else {
								if (x[1] <= 0.5) {
									if (x[3] <= 0.5) {
										if (x[6] <= 0.5) {
											if (x[7] <= 2.0) {
												return 0.0f;
											}
											else {
												return 4.0f;
											}

										}
										else {
											return 0.0f;
										}

									}
									else {
										if (x[8] <= 6.5) {
											return 21.0f;
										}
										else {
											return 4.0f;
										}

									}

								}
								else {
									return 22.0f;
								}

							}

						}
						else {
							if (x[7] <= 6.0) {
								if (x[1] <= 0.5) {
									if (x[3] <= 0.5) {
										return 18.0f;
									}
									else {
										if (x[12] <= 0.5) {
											return 18.0f;
										}
										else {
											if (x[8] <= 6.5) {
												return 21.0f;
											}
											else {
												return 18.0f;
											}

										}

									}

								}
								else {
									return 18.0f;
								}

							}
							else {
								if (x[3] <= 0.5) {
									return 0.0f;
								}
								else {
									if (x[5] <= 0.5) {
										return 4.0f;
									}
									else {
										return 28.0f;
									}

								}

							}

						}

					}
					else {
						if (x[7] <= 2.0) {
							return 1.0f;
						}
						else {
							if (x[8] <= 8.5) {
								if (x[1] <= 14.5) {
									if (x[8] <= 4.5) {
										if (x[3] <= 0.5) {
											return 14.0f;
										}
										else {
											if (x[11] <= 2.5) {
												return 15.0f;
											}
											else {
												return 14.0f;
											}

										}

									}
									else {
										return 14.0f;
									}

								}
								else {
									if (x[11] <= 2.5) {
										return 0.0f;
									}
									else {
										return 14.0f;
									}

								}

							}
							else {
								if (x[2] <= 0.5) {
									if (x[3] <= 0.5) {
										if (x[8] <= 11.5) {
											if (x[11] <= 2.5) {
												return 0.0f;
											}
											else {
												return 14.0f;
											}

										}
										else {
											return 14.0f;
										}

									}
									else {
										return 12.0f;
									}

								}
								else {
									return 30.0f;
								}

							}

						}

					}

				}
				else {
					if (x[7] <= 10.5) {
						if (x[8] <= 6.0) {
							if (x[12] <= 0.5) {
								if (x[8] <= 4.5) {
									if (x[3] <= 0.5) {
										return 3.0f;
									}
									else {
										return 15.0f;
									}

								}
								else {
									return 3.0f;
								}

							}
							else {
								if (x[1] <= 0.5) {
									if (x[12] <= 1.5) {
										if (x[3] <= 0.5) {
											return 3.0f;
										}
										else {
											return 21.0f;
										}

									}
									else {
										if (x[2] <= 0.5) {
											return 2.0f;
										}
										else {
											return 16.0f;
										}

									}

								}
								else {
									return 22.0f;
								}

							}

						}
						else {
							if (x[12] <= 5.5) {
								return 3.0f;
							}
							else {
								return 20.0f;
							}

						}

					}
					else {
						if (x[11] <= 5.5) {
							if (x[12] <= 0.5) {
								if (x[1] <= 0.5) {
									if (x[8] <= 4.5) {
										return 15.0f;
									}
									else {
										if (x[8] <= 6.5) {
											return 0.0f;
										}
										else {
											if (x[5] <= 0.5) {
												return 4.0f;
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
								if (x[1] <= 0.5) {
									if (x[8] <= 8.5) {
										if (x[3] <= 0.5) {
											if (x[11] <= 2.5) {
												return 0.0f;
											}
											else {
												return 16.0f;
											}

										}
										else {
											if (x[8] <= 6.5) {
												return 21.0f;
											}
											else {
												return 4.0f;
											}

										}

									}
									else {
										return 0.0f;
									}

								}
								else {
									return 22.0f;
								}

							}

						}
						else {
							return 17.0f;
						}

					}

				}

			}
			else {
				if (x[11] <= 3.5) {
					if (x[11] <= 2.5) {
						if (x[12] <= 5.5) {
							if (x[8] <= 4.5) {
								if (x[8] <= 2.5) {
									return 0.0f;
								}
								else {
									return 11.0f;
								}

							}
							else {
								if (x[12] <= 0.5) {
									return 0.0f;
								}
								else {
									if (x[8] <= 8.5) {
										return 4.0f;
									}
									else {
										return 0.0f;
									}

								}

							}

						}
						else {
							return 20.0f;
						}

					}
					else {
						if (x[7] <= 9.5) {
							if (x[8] <= 10.0) {
								if (x[8] <= 4.5) {
									if (x[8] <= 2.5) {
										return 0.0f;
									}
									else {
										return 11.0f;
									}

								}
								else {
									return 0.0f;
								}

							}
							else {
								if (x[8] <= 11.5) {
									if (x[2] <= 0.5) {
										return 10.0f;
									}
									else {
										return 20.0f;
									}

								}
								else {
									return 0.0f;
								}

							}

						}
						else {
							return 5.0f;
						}

					}

				}
				else {
					if (x[5] <= 1.0) {
						return 5.0f;
					}
					else {
						if (x[12] <= 3.5) {
							return 0.0f;
						}
						else {
							return 5.0f;
						}

					}

				}

			}

		}
		else {
			if (x[7] <= 6.0) {
				return 19.0f;
			}
			else {
				if (x[11] <= 1.5) {
					if (x[3] <= 0.5) {
						return 0.0f;
					}
					else {
						if (x[5] <= 0.5) {
							return 4.0f;
						}
						else {
							return 28.0f;
						}

					}

				}
				else {
					return 30.0f;
				}

			}

		}

	}

}