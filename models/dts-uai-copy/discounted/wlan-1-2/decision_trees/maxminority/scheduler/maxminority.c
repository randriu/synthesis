#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f,0.f,0.f,0.f,1.f,1.f,0.f,0.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[12] <= 0.5) {
		if (x[0] <= 5.5) {
			if (x[1] <= 3.5) {
				if (x[8] <= 8.5) {
					if (x[1] <= 0.5) {
						if (x[8] <= 6.5) {
							if (x[8] <= 4.5) {
								if (x[2] <= 0.5) {
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
							if (x[2] <= 0.5) {
								if (x[7] <= 8.5) {
									return 3.0f;
								}
								else {
									return 4.0f;
								}

							}
							else {
								if (x[7] <= 6.5) {
									if (x[0] <= 0.5) {
										return 0.0f;
									}
									else {
										return 4.0f;
									}

								}
								else {
									if (x[4] <= 0.5) {
										return 3.0f;
									}
									else {
										return 4.0f;
									}

								}

							}

						}

					}
					else {
						if (x[4] <= 0.5) {
							if (x[8] <= 5.5) {
								if (x[1] <= 1.5) {
									if (x[0] <= 0.5) {
										if (x[2] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 6.5) {
												return 0.0f;
											}
											else {
												return 3.0f;
											}

										}

									}
									else {
										return 0.0f;
									}

								}
								else {
									if (x[1] <= 2.5) {
										if (x[0] <= 0.5) {
											if (x[2] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 6.5) {
													return 0.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											return 0.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[2] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 6.5) {
													return 0.0f;
												}
												else {
													return 3.0f;
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
								if (x[2] <= 0.5) {
									if (x[8] <= 6.5) {
										return 20.0f;
									}
									else {
										return 0.0f;
									}

								}
								else {
									if (x[8] <= 6.5) {
										return 20.0f;
									}
									else {
										return 3.0f;
									}

								}

							}

						}
						else {
							if (x[7] <= 9.5) {
								if (x[8] <= 5.5) {
									return 18.0f;
								}
								else {
									if (x[11] <= 3.5) {
										return 0.0f;
									}
									else {
										return 5.0f;
									}

								}

							}
							else {
								if (x[8] <= 6.5) {
									if (x[11] <= 2.5) {
										return 0.0f;
									}
									else {
										return 5.0f;
									}

								}
								else {
									return 22.0f;
								}

							}

						}

					}

				}
				else {
					if (x[0] <= 2.5) {
						if (x[3] <= 0.5) {
							if (x[0] <= 0.5) {
								if (x[4] <= 0.5) {
									if (x[2] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 6.5) {
											if (x[11] <= 0.5) {
												return 0.0f;
											}
											else {
												return 15.0f;
											}

										}
										else {
											return 3.0f;
										}

									}

								}
								else {
									if (x[7] <= 9.5) {
										if (x[11] <= 3.5) {
											return 0.0f;
										}
										else {
											return 5.0f;
										}

									}
									else {
										if (x[11] <= 2.5) {
											return 0.0f;
										}
										else {
											return 5.0f;
										}

									}

								}

							}
							else {
								if (x[0] <= 1.5) {
									if (x[7] <= 5.5) {
										if (x[11] <= 0.5) {
											return 0.0f;
										}
										else {
											return 13.0f;
										}

									}
									else {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											if (x[11] <= 1.5) {
												return 0.0f;
											}
											else {
												return 25.0f;
											}

										}

									}

								}
								else {
									if (x[7] <= 5.5) {
										if (x[11] <= 0.5) {
											return 0.0f;
										}
										else {
											return 13.0f;
										}

									}
									else {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											if (x[11] <= 1.5) {
												return 0.0f;
											}
											else {
												return 25.0f;
											}

										}

									}

								}

							}

						}
						else {
							if (x[5] <= 0.5) {
								if (x[7] <= 6.5) {
									return 21.0f;
								}
								else {
									return 4.0f;
								}

							}
							else {
								if (x[0] <= 1.5) {
									if (x[0] <= 0.5) {
										if (x[2] <= 0.5) {
											return 0.0f;
										}
										else {
											return 5.0f;
										}

									}
									else {
										if (x[7] <= 5.5) {
											return 19.0f;
										}
										else {
											if (x[7] <= 6.5) {
												return 0.0f;
											}
											else {
												return 23.0f;
											}

										}

									}

								}
								else {
									if (x[7] <= 5.5) {
										return 19.0f;
									}
									else {
										if (x[7] <= 6.5) {
											return 0.0f;
										}
										else {
											return 23.0f;
										}

									}

								}

							}

						}

					}
					else {
						if (x[3] <= 0.5) {
							if (x[0] <= 3.5) {
								if (x[7] <= 5.5) {
									if (x[11] <= 0.5) {
										return 0.0f;
									}
									else {
										return 13.0f;
									}

								}
								else {
									if (x[7] <= 6.5) {
										return 21.0f;
									}
									else {
										if (x[11] <= 1.5) {
											return 0.0f;
										}
										else {
											return 25.0f;
										}

									}

								}

							}
							else {
								if (x[0] <= 4.5) {
									if (x[7] <= 5.5) {
										if (x[11] <= 0.5) {
											return 0.0f;
										}
										else {
											return 13.0f;
										}

									}
									else {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											if (x[11] <= 1.5) {
												return 0.0f;
											}
											else {
												return 25.0f;
											}

										}

									}

								}
								else {
									if (x[7] <= 5.5) {
										if (x[11] <= 0.5) {
											return 0.0f;
										}
										else {
											return 13.0f;
										}

									}
									else {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											if (x[11] <= 1.5) {
												return 0.0f;
											}
											else {
												return 25.0f;
											}

										}

									}

								}

							}

						}
						else {
							if (x[5] <= 0.5) {
								if (x[7] <= 6.5) {
									return 21.0f;
								}
								else {
									return 4.0f;
								}

							}
							else {
								if (x[7] <= 5.5) {
									return 19.0f;
								}
								else {
									if (x[7] <= 6.5) {
										return 0.0f;
									}
									else {
										return 23.0f;
									}

								}

							}

						}

					}

				}

			}
			else {
				if (x[4] <= 0.5) {
					if (x[8] <= 5.5) {
						if (x[1] <= 8.5) {
							if (x[1] <= 5.5) {
								if (x[1] <= 4.5) {
									if (x[0] <= 0.5) {
										if (x[2] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 6.5) {
												return 0.0f;
											}
											else {
												return 3.0f;
											}

										}

									}
									else {
										return 0.0f;
									}

								}
								else {
									if (x[0] <= 0.5) {
										if (x[2] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 6.5) {
												return 0.0f;
											}
											else {
												return 3.0f;
											}

										}

									}
									else {
										return 0.0f;
									}

								}

							}
							else {
								if (x[1] <= 6.5) {
									if (x[0] <= 0.5) {
										if (x[2] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 6.5) {
												return 0.0f;
											}
											else {
												return 3.0f;
											}

										}

									}
									else {
										return 0.0f;
									}

								}
								else {
									if (x[1] <= 7.5) {
										if (x[0] <= 0.5) {
											if (x[2] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 6.5) {
													return 0.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											return 0.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[2] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 6.5) {
													return 0.0f;
												}
												else {
													return 3.0f;
												}

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
							if (x[1] <= 11.5) {
								if (x[1] <= 9.5) {
									if (x[0] <= 0.5) {
										if (x[2] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 6.5) {
												return 0.0f;
											}
											else {
												return 3.0f;
											}

										}

									}
									else {
										return 0.0f;
									}

								}
								else {
									if (x[1] <= 10.5) {
										if (x[0] <= 0.5) {
											if (x[2] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 6.5) {
													return 0.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											return 0.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[2] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 6.5) {
													return 0.0f;
												}
												else {
													return 3.0f;
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
								if (x[1] <= 12.5) {
									if (x[0] <= 0.5) {
										if (x[2] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 6.5) {
												return 0.0f;
											}
											else {
												return 3.0f;
											}

										}

									}
									else {
										return 0.0f;
									}

								}
								else {
									if (x[1] <= 13.5) {
										if (x[0] <= 0.5) {
											if (x[2] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 6.5) {
													return 0.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											return 0.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[1] <= 14.5) {
												if (x[2] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 6.5) {
														return 0.0f;
													}
													else {
														return 3.0f;
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

						}

					}
					else {
						if (x[2] <= 0.5) {
							if (x[8] <= 6.5) {
								return 20.0f;
							}
							else {
								return 0.0f;
							}

						}
						else {
							if (x[8] <= 6.5) {
								return 20.0f;
							}
							else {
								return 3.0f;
							}

						}

					}

				}
				else {
					if (x[7] <= 9.5) {
						if (x[8] <= 5.5) {
							return 18.0f;
						}
						else {
							if (x[11] <= 3.5) {
								return 0.0f;
							}
							else {
								return 5.0f;
							}

						}

					}
					else {
						if (x[8] <= 6.5) {
							if (x[11] <= 2.5) {
								return 0.0f;
							}
							else {
								return 5.0f;
							}

						}
						else {
							return 22.0f;
						}

					}

				}

			}

		}
		else {
			if (x[11] <= 0.5) {
				if (x[0] <= 9.5) {
					if (x[0] <= 7.5) {
						if (x[0] <= 6.5) {
							if (x[5] <= 0.5) {
								if (x[7] <= 5.5) {
									if (x[1] <= 0.5) {
										if (x[3] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 6.5) {
												return 0.0f;
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
									if (x[3] <= 0.5) {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 0.0f;
										}

									}
									else {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 4.0f;
										}

									}

								}

							}
							else {
								if (x[7] <= 5.5) {
									return 19.0f;
								}
								else {
									if (x[7] <= 6.5) {
										return 0.0f;
									}
									else {
										return 23.0f;
									}

								}

							}

						}
						else {
							if (x[5] <= 0.5) {
								if (x[7] <= 5.5) {
									if (x[1] <= 0.5) {
										if (x[3] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 6.5) {
												return 0.0f;
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
									if (x[3] <= 0.5) {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 0.0f;
										}

									}
									else {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 4.0f;
										}

									}

								}

							}
							else {
								if (x[7] <= 5.5) {
									return 19.0f;
								}
								else {
									if (x[7] <= 6.5) {
										return 0.0f;
									}
									else {
										return 23.0f;
									}

								}

							}

						}

					}
					else {
						if (x[0] <= 8.5) {
							if (x[7] <= 5.5) {
								if (x[5] <= 0.5) {
									if (x[8] <= 4.5) {
										return 12.0f;
									}
									else {
										if (x[1] <= 0.5) {
											if (x[3] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 6.5) {
													return 0.0f;
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

								}
								else {
									return 19.0f;
								}

							}
							else {
								if (x[5] <= 0.5) {
									if (x[3] <= 0.5) {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 0.0f;
										}

									}
									else {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 4.0f;
										}

									}

								}
								else {
									if (x[7] <= 6.5) {
										return 0.0f;
									}
									else {
										return 23.0f;
									}

								}

							}

						}
						else {
							if (x[7] <= 5.5) {
								if (x[5] <= 0.5) {
									if (x[8] <= 4.5) {
										return 12.0f;
									}
									else {
										if (x[1] <= 0.5) {
											if (x[3] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 6.5) {
													return 0.0f;
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

								}
								else {
									return 19.0f;
								}

							}
							else {
								if (x[5] <= 0.5) {
									if (x[3] <= 0.5) {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 0.0f;
										}

									}
									else {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 4.0f;
										}

									}

								}
								else {
									if (x[7] <= 6.5) {
										return 0.0f;
									}
									else {
										return 23.0f;
									}

								}

							}

						}

					}

				}
				else {
					if (x[0] <= 11.5) {
						if (x[0] <= 10.5) {
							if (x[7] <= 5.5) {
								if (x[5] <= 0.5) {
									if (x[8] <= 4.5) {
										return 12.0f;
									}
									else {
										if (x[1] <= 0.5) {
											if (x[3] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 6.5) {
													return 0.0f;
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

								}
								else {
									return 19.0f;
								}

							}
							else {
								if (x[5] <= 0.5) {
									if (x[3] <= 0.5) {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 0.0f;
										}

									}
									else {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 4.0f;
										}

									}

								}
								else {
									if (x[7] <= 6.5) {
										return 0.0f;
									}
									else {
										return 23.0f;
									}

								}

							}

						}
						else {
							if (x[5] <= 0.5) {
								if (x[7] <= 5.5) {
									if (x[1] <= 0.5) {
										if (x[3] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 6.5) {
												return 0.0f;
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
									if (x[3] <= 0.5) {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 0.0f;
										}

									}
									else {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 4.0f;
										}

									}

								}

							}
							else {
								if (x[7] <= 5.5) {
									return 19.0f;
								}
								else {
									if (x[7] <= 6.5) {
										return 0.0f;
									}
									else {
										return 23.0f;
									}

								}

							}

						}

					}
					else {
						if (x[0] <= 12.5) {
							if (x[7] <= 5.5) {
								if (x[5] <= 0.5) {
									if (x[8] <= 4.5) {
										return 12.0f;
									}
									else {
										if (x[1] <= 0.5) {
											if (x[3] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 6.5) {
													return 0.0f;
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

								}
								else {
									return 19.0f;
								}

							}
							else {
								if (x[5] <= 0.5) {
									if (x[3] <= 0.5) {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 0.0f;
										}

									}
									else {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 4.0f;
										}

									}

								}
								else {
									if (x[7] <= 6.5) {
										return 0.0f;
									}
									else {
										return 23.0f;
									}

								}

							}

						}
						else {
							if (x[7] <= 5.5) {
								if (x[5] <= 0.5) {
									if (x[8] <= 4.5) {
										return 12.0f;
									}
									else {
										if (x[0] <= 13.5) {
											if (x[1] <= 0.5) {
												if (x[3] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 6.5) {
														return 0.0f;
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
											return 0.0f;
										}

									}

								}
								else {
									return 19.0f;
								}

							}
							else {
								if (x[5] <= 0.5) {
									if (x[3] <= 0.5) {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 0.0f;
										}

									}
									else {
										if (x[7] <= 6.5) {
											return 21.0f;
										}
										else {
											return 4.0f;
										}

									}

								}
								else {
									if (x[7] <= 6.5) {
										return 0.0f;
									}
									else {
										return 23.0f;
									}

								}

							}

						}

					}

				}

			}
			else {
				if (x[7] <= 6.0) {
					if (x[8] <= 4.5) {
						if (x[0] <= 12.5) {
							return 12.0f;
						}
						else {
							if (x[0] <= 14.5) {
								return 14.0f;
							}
							else {
								return 12.0f;
							}

						}

					}
					else {
						return 13.0f;
					}

				}
				else {
					if (x[11] <= 1.5) {
						return 0.0f;
					}
					else {
						return 25.0f;
					}

				}

			}

		}

	}
	else {
		if (x[11] <= 0.5) {
			if (x[8] <= 6.0) {
				if (x[3] <= 0.5) {
					if (x[12] <= 2.5) {
						if (x[0] <= 0.5) {
							if (x[2] <= 0.5) {
								return 2.0f;
							}
							else {
								if (x[7] <= 4.5) {
									return 10.0f;
								}
								else {
									return 11.0f;
								}

							}

						}
						else {
							if (x[0] <= 1.5) {
								return 11.0f;
							}
							else {
								return 0.0f;
							}

						}

					}
					else {
						return 11.0f;
					}

				}
				else {
					if (x[1] <= 0.5) {
						return 16.0f;
					}
					else {
						return 17.0f;
					}

				}

			}
			else {
				if (x[12] <= 2.5) {
					if (x[1] <= 6.5) {
						if (x[1] <= 2.5) {
							if (x[1] <= 0.5) {
								if (x[4] <= 0.5) {
									if (x[5] <= 0.5) {
										return 3.0f;
									}
									else {
										return 0.0f;
									}

								}
								else {
									return 4.0f;
								}

							}
							else {
								if (x[12] <= 1.5) {
									return 0.0f;
								}
								else {
									return 24.0f;
								}

							}

						}
						else {
							if (x[12] <= 1.5) {
								return 0.0f;
							}
							else {
								return 24.0f;
							}

						}

					}
					else {
						if (x[12] <= 1.5) {
							return 0.0f;
						}
						else {
							return 24.0f;
						}

					}

				}
				else {
					if (x[0] <= 5.5) {
						if (x[0] <= 1.5) {
							if (x[0] <= 0.5) {
								if (x[3] <= 0.5) {
									if (x[5] <= 1.0) {
										return 8.0f;
									}
									else {
										return 6.0f;
									}

								}
								else {
									if (x[8] <= 9.5) {
										if (x[12] <= 3.5) {
											return 0.0f;
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
							else {
								if (x[8] <= 9.5) {
									if (x[12] <= 3.5) {
										return 0.0f;
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
						else {
							if (x[0] <= 3.5) {
								if (x[0] <= 2.5) {
									if (x[8] <= 9.5) {
										if (x[12] <= 3.5) {
											return 0.0f;
										}
										else {
											return 6.0f;
										}

									}
									else {
										return 6.0f;
									}

								}
								else {
									if (x[8] <= 9.5) {
										if (x[12] <= 3.5) {
											return 0.0f;
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
							else {
								if (x[0] <= 4.5) {
									if (x[8] <= 9.5) {
										if (x[12] <= 3.5) {
											return 0.0f;
										}
										else {
											return 6.0f;
										}

									}
									else {
										return 6.0f;
									}

								}
								else {
									if (x[8] <= 9.5) {
										if (x[12] <= 3.5) {
											return 0.0f;
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
						if (x[0] <= 9.5) {
							if (x[0] <= 7.5) {
								if (x[0] <= 6.5) {
									if (x[8] <= 9.5) {
										if (x[12] <= 3.5) {
											return 0.0f;
										}
										else {
											return 6.0f;
										}

									}
									else {
										return 6.0f;
									}

								}
								else {
									if (x[8] <= 9.5) {
										if (x[12] <= 3.5) {
											return 0.0f;
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
							else {
								if (x[0] <= 8.5) {
									if (x[8] <= 9.5) {
										if (x[12] <= 3.5) {
											return 0.0f;
										}
										else {
											return 6.0f;
										}

									}
									else {
										return 6.0f;
									}

								}
								else {
									if (x[8] <= 9.5) {
										if (x[12] <= 3.5) {
											return 0.0f;
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
						else {
							if (x[0] <= 11.5) {
								if (x[0] <= 10.5) {
									if (x[8] <= 9.5) {
										if (x[12] <= 3.5) {
											return 0.0f;
										}
										else {
											return 6.0f;
										}

									}
									else {
										return 6.0f;
									}

								}
								else {
									if (x[8] <= 9.5) {
										if (x[12] <= 3.5) {
											return 0.0f;
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
							else {
								if (x[0] <= 12.5) {
									if (x[8] <= 9.5) {
										if (x[12] <= 3.5) {
											return 0.0f;
										}
										else {
											return 6.0f;
										}

									}
									else {
										return 6.0f;
									}

								}
								else {
									if (x[8] <= 9.5) {
										if (x[12] <= 3.5) {
											return 0.0f;
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

				}

			}

		}
		else {
			if (x[0] <= 0.5) {
				if (x[2] <= 0.5) {
					if (x[7] <= 6.0) {
						if (x[6] <= 0.5) {
							if (x[11] <= 1.5) {
								return 0.0f;
							}
							else {
								return 1.0f;
							}

						}
						else {
							if (x[11] <= 1.5) {
								return 0.0f;
							}
							else {
								return 9.0f;
							}

						}

					}
					else {
						if (x[4] <= 1.0) {
							if (x[11] <= 5.5) {
								return 0.0f;
							}
							else {
								return 7.0f;
							}

						}
						else {
							if (x[11] <= 3.5) {
								return 0.0f;
							}
							else {
								return 5.0f;
							}

						}

					}

				}
				else {
					if (x[7] <= 6.5) {
						return 15.0f;
					}
					else {
						return 16.0f;
					}

				}

			}
			else {
				if (x[0] <= 12.5) {
					if (x[0] <= 7.5) {
						if (x[0] <= 1.5) {
							return 13.0f;
						}
						else {
							if (x[0] <= 2.5) {
								return 13.0f;
							}
							else {
								if (x[0] <= 3.5) {
									return 13.0f;
								}
								else {
									if (x[0] <= 4.5) {
										return 13.0f;
									}
									else {
										if (x[0] <= 5.5) {
											return 13.0f;
										}
										else {
											if (x[0] <= 6.5) {
												return 13.0f;
											}
											else {
												if (x[3] <= 0.5) {
													return 11.0f;
												}
												else {
													return 13.0f;
												}

											}

										}

									}

								}

							}

						}

					}
					else {
						if (x[0] <= 8.5) {
							if (x[3] <= 0.5) {
								return 11.0f;
							}
							else {
								return 13.0f;
							}

						}
						else {
							if (x[0] <= 9.5) {
								return 13.0f;
							}
							else {
								if (x[0] <= 10.5) {
									return 13.0f;
								}
								else {
									if (x[0] <= 11.5) {
										return 13.0f;
									}
									else {
										if (x[3] <= 0.5) {
											return 11.0f;
										}
										else {
											return 13.0f;
										}

									}

								}

							}

						}

					}

				}
				else {
					if (x[3] <= 0.5) {
						return 11.0f;
					}
					else {
						return 13.0f;
					}

				}

			}

		}

	}

}