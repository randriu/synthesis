#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f,0.f,3.f,3.f,1.f,4.f,4.f,1.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[3] <= 1.5) {
		if (x[3] <= 0.5) {
			if (x[8] <= 2.5) {
				if (x[4] <= 4.5) {
					return 0.0f;
				}
				else {
					return 5.0f;
				}

			}
			else {
				if (x[4] <= 8.5) {
					if (x[5] <= 7.5) {
						if (x[7] <= 6.5) {
							if (x[5] <= 6.5) {
								if (x[4] <= 6.5) {
									return 0.0f;
								}
								else {
									if (x[10] <= 1.5) {
										if (x[7] <= 5.5) {
											if (x[4] <= 7.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 5.0f;
												}
												else {
													if (x[7] <= 4.5) {
														return 0.0f;
													}
													else {
														return 5.0f;
													}

												}

											}

										}
										else {
											return 5.0f;
										}

									}
									else {
										return 0.0f;
									}

								}

							}
							else {
								if (x[7] <= 1.5) {
									return 5.0f;
								}
								else {
									if (x[10] <= 1.5) {
										if (x[7] <= 3.5) {
											return 5.0f;
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
							if (x[5] <= 5.0) {
								return 5.0f;
							}
							else {
								return 0.0f;
							}

						}

					}
					else {
						if (x[4] <= 7.5) {
							if (x[2] <= 1.5) {
								if (x[7] <= 6.5) {
									if (x[10] <= 1.5) {
										return 5.0f;
									}
									else {
										if (x[7] <= 3.5) {
											if (x[10] <= 4.5) {
												return 5.0f;
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
									return 0.0f;
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
					if (x[7] <= 4.5) {
						if (x[4] <= 9.5) {
							if (x[10] <= 2.5) {
								if (x[7] <= 2.5) {
									return 5.0f;
								}
								else {
									if (x[7] <= 3.5) {
										return 0.0f;
									}
									else {
										return 5.0f;
									}

								}

							}
							else {
								if (x[7] <= 1.5) {
									if (x[0] <= 1.0) {
										return 5.0f;
									}
									else {
										if (x[10] <= 3.5) {
											return 0.0f;
										}
										else {
											return 5.0f;
										}

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
					else {
						if (x[0] <= 1.0) {
							if (x[4] <= 9.5) {
								if (x[2] <= 2.5) {
									if (x[7] <= 6.5) {
										if (x[10] <= 5.5) {
											return 0.0f;
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
									return 5.0f;
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

			}

		}
		else {
			if (x[5] <= 0.5) {
				if (x[9] <= 2.5) {
					return 6.0f;
				}
				else {
					if (x[4] <= 9.5) {
						if (x[7] <= 4.5) {
							if (x[6] <= 5.5) {
								if (x[0] <= 1.5) {
									if (x[4] <= 8.5) {
										if (x[2] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[7] <= 1.5) {
												if (x[10] <= 2.0) {
													if (x[4] <= 7.5) {
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
												return 1.0f;
											}

										}

									}
									else {
										if (x[7] <= 2.5) {
											if (x[10] <= 2.5) {
												return 6.0f;
											}
											else {
												if (x[2] <= 0.5) {
													return 1.0f;
												}
												else {
													if (x[1] <= 1.0) {
														return 6.0f;
													}
													else {
														if (x[10] <= 3.5) {
															return 1.0f;
														}
														else {
															return 6.0f;
														}

													}

												}

											}

										}
										else {
											if (x[7] <= 3.5) {
												return 1.0f;
											}
											else {
												if (x[2] <= 1.0) {
													return 6.0f;
												}
												else {
													return 1.0f;
												}

											}

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
						else {
							if (x[6] <= 3.5) {
								return 6.0f;
							}
							else {
								if (x[6] <= 8.5) {
									if (x[10] <= 3.5) {
										if (x[7] <= 6.5) {
											return 6.0f;
										}
										else {
											return 1.0f;
										}

									}
									else {
										if (x[7] <= 6.5) {
											if (x[10] <= 5.5) {
												return 1.0f;
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
									return 6.0f;
								}

							}

						}

					}
					else {
						return 6.0f;
					}

				}

			}
			else {
				if (x[6] <= 7.5) {
					if (x[6] <= 6.5) {
						if (x[2] <= 2.5) {
							return 1.0f;
						}
						else {
							if (x[6] <= 3.5) {
								return 1.0f;
							}
							else {
								return 6.0f;
							}

						}

					}
					else {
						if (x[7] <= 1.5) {
							return 6.0f;
						}
						else {
							if (x[10] <= 1.5) {
								if (x[7] <= 3.5) {
									return 6.0f;
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
					if (x[5] <= 6.5) {
						if (x[4] <= 7.5) {
							if (x[2] <= 1.5) {
								if (x[7] <= 3.5) {
									return 6.0f;
								}
								else {
									if (x[10] <= 1.5) {
										return 6.0f;
									}
									else {
										return 1.0f;
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
					else {
						return 1.0f;
					}

				}

			}

		}

	}
	else {
		if (x[6] <= 0.5) {
			if (x[5] <= 0.5) {
				return 7.0f;
			}
			else {
				if (x[2] <= 1.5) {
					if (x[0] <= 1.0) {
						if (x[10] <= 4.5) {
							return 4.0f;
						}
						else {
							return 2.0f;
						}

					}
					else {
						if (x[10] <= 3.5) {
							if (x[2] <= 0.5) {
								if (x[4] <= 6.5) {
									return 3.0f;
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
							return 3.0f;
						}

					}

				}
				else {
					return 2.0f;
				}

			}

		}
		else {
			if (x[7] <= 2.5) {
				return 2.0f;
			}
			else {
				if (x[10] <= 3.5) {
					if (x[10] <= 1.5) {
						if (x[7] <= 3.5) {
							if (x[4] <= 3.5) {
								if (x[0] <= 1.5) {
									return 3.0f;
								}
								else {
									return 4.0f;
								}

							}
							else {
								return 3.0f;
							}

						}
						else {
							if (x[7] <= 5.5) {
								return 2.0f;
							}
							else {
								if (x[7] <= 6.5) {
									return 3.0f;
								}
								else {
									if (x[7] <= 7.5) {
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
						return 2.0f;
					}

				}
				else {
					if (x[7] <= 4.5) {
						if (x[7] <= 3.5) {
							if (x[10] <= 4.5) {
								return 3.0f;
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
						if (x[10] <= 4.5) {
							if (x[1] <= 1.0) {
								if (x[5] <= 7.0) {
									return 4.0f;
								}
								else {
									return 3.0f;
								}

							}
							else {
								if (x[0] <= 1.0) {
									return 4.0f;
								}
								else {
									if (x[4] <= 7.5) {
										return 4.0f;
									}
									else {
										return 3.0f;
									}

								}

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

}