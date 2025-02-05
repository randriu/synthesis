#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {1.f,1.f,0.f,2.f,2.f,5.f,5.f,3.f,5.f,5.f,1.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[6] <= 0.5) {
		if (x[5] <= 0.5) {
			return 4.0f;
		}
		else {
			if (x[0] <= 0.5) {
				if (x[5] <= 6.5) {
					return 1.0f;
				}
				else {
					if (x[2] <= 1.0) {
						return 1.0f;
					}
					else {
						return 0.0f;
					}

				}

			}
			else {
				if (x[0] <= 2.5) {
					return 0.0f;
				}
				else {
					if (x[1] <= 1.5) {
						return 0.0f;
					}
					else {
						if (x[2] <= 1.0) {
							return 0.0f;
						}
						else {
							return 1.0f;
						}

					}

				}

			}

		}

	}
	else {
		if (x[4] <= 21.5) {
			if (x[7] <= 4.0) {
				if (x[5] <= 4.5) {
					if (x[4] <= 17.5) {
						if (x[0] <= 2.5) {
							if (x[6] <= 4.5) {
								return 1.0f;
							}
							else {
								if (x[1] <= 2.5) {
									if (x[4] <= 8.5) {
										return 1.0f;
									}
									else {
										if (x[6] <= 7.5) {
											return 3.0f;
										}
										else {
											return 1.0f;
										}

									}

								}
								else {
									return 1.0f;
								}

							}

						}
						else {
							return 0.0f;
						}

					}
					else {
						if (x[1] <= 2.5) {
							if (x[5] <= 3.5) {
								if (x[5] <= 2.5) {
									return 1.0f;
								}
								else {
									if (x[6] <= 2.5) {
										return 1.0f;
									}
									else {
										if (x[0] <= 2.0) {
											return 0.0f;
										}
										else {
											if (x[9] <= 1.5) {
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
						else {
							if (x[5] <= 2.5) {
								return 1.0f;
							}
							else {
								return 0.0f;
							}

						}

					}

				}
				else {
					if (x[0] <= 2.5) {
						if (x[1] <= 1.5) {
							if (x[5] <= 8.0) {
								if (x[4] <= 8.5) {
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
						else {
							return 3.0f;
						}

					}
					else {
						if (x[1] <= 2.5) {
							return 3.0f;
						}
						else {
							return 1.0f;
						}

					}

				}

			}
			else {
				if (x[6] <= 6.5) {
					if (x[1] <= 2.5) {
						if (x[0] <= 0.5) {
							if (x[4] <= 11.0) {
								return 0.0f;
							}
							else {
								return 1.0f;
							}

						}
						else {
							if (x[9] <= 3.5) {
								if (x[1] <= 0.5) {
									return 1.0f;
								}
								else {
									if (x[4] <= 18.5) {
										if (x[2] <= 1.0) {
											if (x[0] <= 1.5) {
												if (x[1] <= 1.5) {
													return 0.0f;
												}
												else {
													return 1.0f;
												}

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
											return 1.0f;
										}

									}
									else {
										return 0.0f;
									}

								}

							}
							else {
								return 1.0f;
							}

						}

					}
					else {
						return 1.0f;
					}

				}
				else {
					if (x[5] <= 8.5) {
						if (x[8] <= 3.5) {
							if (x[8] <= 2.5) {
								if (x[0] <= 2.5) {
									if (x[5] <= 2.5) {
										return 0.0f;
									}
									else {
										if (x[4] <= 18.5) {
											if (x[4] <= 15.5) {
												if (x[4] <= 12.5) {
													return 0.0f;
												}
												else {
													if (x[6] <= 7.5) {
														return 0.0f;
													}
													else {
														return 1.0f;
													}

												}

											}
											else {
												if (x[9] <= 2.5) {
													return 0.0f;
												}
												else {
													if (x[1] <= 0.5) {
														return 1.0f;
													}
													else {
														if (x[2] <= 1.0) {
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
											if (x[0] <= 1.5) {
												return 1.0f;
											}
											else {
												if (x[1] <= 1.0) {
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
									if (x[4] <= 12.0) {
										return 2.0f;
									}
									else {
										return 1.0f;
									}

								}

							}
							else {
								if (x[7] <= 9.0) {
									return 0.0f;
								}
								else {
									if (x[1] <= 1.5) {
										return 3.0f;
									}
									else {
										return 0.0f;
									}

								}

							}

						}
						else {
							if (x[0] <= 2.0) {
								if (x[5] <= 3.5) {
									return 1.0f;
								}
								else {
									if (x[1] <= 1.5) {
										if (x[5] <= 6.5) {
											if (x[5] <= 5.5) {
												if (x[6] <= 8.5) {
													return 2.0f;
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
											return 3.0f;
										}

									}
									else {
										if (x[9] <= 3.5) {
											return 1.0f;
										}
										else {
											return 3.0f;
										}

									}

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

			}

		}
		else {
			if (x[2] <= 1.5) {
				if (x[1] <= 0.5) {
					if (x[4] <= 26.5) {
						if (x[6] <= 8.5) {
							if (x[9] <= 5.0) {
								return 1.0f;
							}
							else {
								if (x[0] <= 1.0) {
									return 2.0f;
								}
								else {
									return 0.0f;
								}

							}

						}
						else {
							if (x[4] <= 24.0) {
								if (x[0] <= 0.5) {
									return 2.0f;
								}
								else {
									if (x[6] <= 9.5) {
										if (x[7] <= 9.0) {
											return 0.0f;
										}
										else {
											if (x[0] <= 2.5) {
												if (x[5] <= 2.0) {
													return 2.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 2.0f;
											}

										}

									}
									else {
										return 0.0f;
									}

								}

							}
							else {
								if (x[0] <= 0.5) {
									return 0.0f;
								}
								else {
									if (x[6] <= 9.5) {
										if (x[8] <= 3.5) {
											if (x[5] <= 7.0) {
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
										return 2.0f;
									}

								}

							}

						}

					}
					else {
						if (x[9] <= 5.0) {
							if (x[7] <= 7.0) {
								if (x[6] <= 7.0) {
									return 1.0f;
								}
								else {
									if (x[0] <= 0.5) {
										return 1.0f;
									}
									else {
										return 0.0f;
									}

								}

							}
							else {
								return 1.0f;
							}

						}
						else {
							if (x[5] <= 1.5) {
								return 0.0f;
							}
							else {
								return 1.0f;
							}

						}

					}

				}
				else {
					if (x[8] <= 3.5) {
						if (x[10] <= 2.5) {
							if (x[0] <= 2.5) {
								if (x[0] <= 0.5) {
									return 1.0f;
								}
								else {
									if (x[1] <= 2.5) {
										return 0.0f;
									}
									else {
										if (x[6] <= 7.0) {
											return 1.0f;
										}
										else {
											return 0.0f;
										}

									}

								}

							}
							else {
								if (x[9] <= 1.5) {
									if (x[6] <= 3.0) {
										return 1.0f;
									}
									else {
										return 2.0f;
									}

								}
								else {
									return 1.0f;
								}

							}

						}
						else {
							if (x[1] <= 1.5) {
								if (x[6] <= 9.0) {
									if (x[7] <= 8.0) {
										if (x[5] <= 2.0) {
											if (x[0] <= 0.5) {
												if (x[2] <= 0.5) {
													return 1.0f;
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
											if (x[4] <= 26.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

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
								if (x[7] <= 9.0) {
									if (x[9] <= 4.5) {
										if (x[8] <= 1.5) {
											return 0.0f;
										}
										else {
											if (x[4] <= 24.5) {
												return 0.0f;
											}
											else {
												if (x[5] <= 7.0) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

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

						}

					}
					else {
						if (x[0] <= 1.5) {
							if (x[4] <= 24.0) {
								if (x[0] <= 0.5) {
									return 2.0f;
								}
								else {
									return 0.0f;
								}

							}
							else {
								if (x[7] <= 9.0) {
									if (x[9] <= 2.5) {
										if (x[5] <= 2.5) {
											if (x[0] <= 0.5) {
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
										if (x[9] <= 3.5) {
											if (x[0] <= 0.5) {
												return 1.0f;
											}
											else {
												return 2.0f;
											}

										}
										else {
											if (x[4] <= 26.5) {
												return 1.0f;
											}
											else {
												return 2.0f;
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
							return 0.0f;
						}

					}

				}

			}
			else {
				if (x[10] <= 2.5) {
					if (x[4] <= 22.5) {
						if (x[7] <= 4.5) {
							return 1.0f;
						}
						else {
							return 0.0f;
						}

					}
					else {
						if (x[5] <= 4.5) {
							return 0.0f;
						}
						else {
							if (x[5] <= 5.5) {
								return 3.0f;
							}
							else {
								if (x[4] <= 27.0) {
									return 0.0f;
								}
								else {
									if (x[0] <= 1.5) {
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
					if (x[7] <= 4.0) {
						if (x[8] <= 3.0) {
							if (x[6] <= 4.5) {
								return 2.0f;
							}
							else {
								if (x[0] <= 1.5) {
									if (x[1] <= 2.5) {
										return 3.0f;
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
							if (x[0] <= 1.5) {
								return 1.0f;
							}
							else {
								return 0.0f;
							}

						}

					}
					else {
						if (x[8] <= 3.5) {
							if (x[7] <= 7.0) {
								return 0.0f;
							}
							else {
								if (x[6] <= 9.5) {
									if (x[1] <= 1.5) {
										if (x[4] <= 25.5) {
											return 0.0f;
										}
										else {
											return 1.0f;
										}

									}
									else {
										if (x[8] <= 2.0) {
											return 0.0f;
										}
										else {
											if (x[0] <= 2.0) {
												return 1.0f;
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

						}
						else {
							if (x[4] <= 26.5) {
								return 0.0f;
							}
							else {
								if (x[8] <= 5.0) {
									if (x[5] <= 3.5) {
										if (x[6] <= 8.5) {
											if (x[1] <= 1.5) {
												return 1.0f;
											}
											else {
												if (x[7] <= 5.5) {
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
										if (x[0] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[1] <= 2.5) {
												return 2.0f;
											}
											else {
												return 1.0f;
											}

										}

									}

								}
								else {
									if (x[1] <= 1.0) {
										return 1.0f;
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

		}

	}

}