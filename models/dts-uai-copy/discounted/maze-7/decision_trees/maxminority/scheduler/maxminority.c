#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,4.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[7] <= 6.5) {
		if (x[2] <= 0.5) {
			if (x[1] <= 0.5) {
				if (x[0] <= 0.5) {
					if (x[8] <= 4.5) {
						if (x[3] <= 0.5) {
							if (x[6] <= 0.5) {
								if (x[7] <= 2.5) {
									if (x[7] <= 1.0) {
										return 0.0f;
									}
									else {
										return 1.0f;
									}

								}
								else {
									if (x[7] <= 3.5) {
										if (x[8] <= 2.5) {
											return 1.0f;
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
								if (x[7] <= 3.5) {
									if (x[7] <= 2.5) {
										if (x[7] <= 1.0) {
											return 0.0f;
										}
										else {
											return 1.0f;
										}

									}
									else {
										if (x[8] <= 2.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[7] <= 4.5) {
										return 3.0f;
									}
									else {
										if (x[8] <= 3.0) {
											return 3.0f;
										}
										else {
											return 1.0f;
										}

									}

								}

							}

						}
						else {
							if (x[4] <= 0.5) {
								if (x[7] <= 3.5) {
									if (x[7] <= 2.5) {
										if (x[7] <= 1.0) {
											return 0.0f;
										}
										else {
											return 1.0f;
										}

									}
									else {
										if (x[8] <= 2.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[7] <= 4.5) {
										return 3.0f;
									}
									else {
										if (x[8] <= 3.0) {
											return 3.0f;
										}
										else {
											return 1.0f;
										}

									}

								}

							}
							else {
								if (x[7] <= 3.5) {
									if (x[7] <= 2.5) {
										if (x[7] <= 1.0) {
											return 0.0f;
										}
										else {
											return 1.0f;
										}

									}
									else {
										if (x[8] <= 2.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[7] <= 4.5) {
										return 3.0f;
									}
									else {
										if (x[8] <= 3.0) {
											return 3.0f;
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
						if (x[8] <= 5.5) {
							if (x[7] <= 1.0) {
								return 0.0f;
							}
							else {
								if (x[3] <= 0.5) {
									if (x[6] <= 0.5) {
										if (x[7] <= 3.0) {
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
								else {
									return 2.0f;
								}

							}

						}
						else {
							if (x[4] <= 0.5) {
								if (x[3] <= 0.5) {
									if (x[7] <= 2.5) {
										if (x[5] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[6] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 2.0f;
												}

											}

										}

									}
									else {
										if (x[6] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[7] <= 3.5) {
												return 1.0f;
											}
											else {
												if (x[7] <= 4.5) {
													return 2.0f;
												}
												else {
													return 1.0f;
												}

											}

										}

									}

								}
								else {
									if (x[7] <= 2.5) {
										if (x[7] <= 1.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[7] <= 4.5) {
											if (x[7] <= 3.5) {
												return 1.0f;
											}
											else {
												return 2.0f;
											}

										}
										else {
											if (x[7] <= 5.5) {
												return 3.0f;
											}
											else {
												return 1.0f;
											}

										}

									}

								}

							}
							else {
								if (x[7] <= 2.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
									}
									else {
										return 2.0f;
									}

								}
								else {
									if (x[7] <= 4.5) {
										if (x[7] <= 3.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[7] <= 5.5) {
											return 3.0f;
										}
										else {
											return 1.0f;
										}

									}

								}

							}

						}

					}

				}
				else {
					if (x[6] <= 0.5) {
						if (x[7] <= 2.5) {
							if (x[7] <= 0.5) {
								if (x[8] <= 3.0) {
									if (x[8] <= 1.5) {
										return 0.0f;
									}
									else {
										return 1.0f;
									}

								}
								else {
									if (x[8] <= 5.5) {
										return 0.0f;
									}
									else {
										return 1.0f;
									}

								}

							}
							else {
								if (x[3] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
									}
									else {
										if (x[8] <= 1.0) {
											return 1.0f;
										}
										else {
											if (x[8] <= 3.0) {
												return 1.0f;
											}
											else {
												if (x[8] <= 4.5) {
													return 1.0f;
												}
												else {
													if (x[8] <= 5.5) {
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
									if (x[4] <= 0.5) {
										if (x[7] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													if (x[8] <= 4.5) {
														return 1.0f;
													}
													else {
														if (x[8] <= 5.5) {
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
										if (x[7] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													if (x[8] <= 4.5) {
														return 1.0f;
													}
													else {
														if (x[8] <= 5.5) {
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

								}

							}

						}
						else {
							if (x[7] <= 3.5) {
								if (x[8] <= 1.5) {
									return 0.0f;
								}
								else {
									if (x[3] <= 0.5) {
										if (x[8] <= 2.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 3.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[4] <= 0.5) {
											if (x[8] <= 2.5) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.5) {
													return 0.0f;
												}
												else {
													return 1.0f;
												}

											}

										}
										else {
											if (x[8] <= 2.5) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.5) {
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
								if (x[8] <= 4.5) {
									if (x[3] <= 0.5) {
										if (x[7] <= 4.5) {
											if (x[8] <= 3.0) {
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
										if (x[4] <= 0.5) {
											if (x[7] <= 4.5) {
												if (x[8] <= 3.0) {
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
											if (x[7] <= 4.5) {
												if (x[8] <= 3.0) {
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

									}

								}
								else {
									if (x[8] <= 5.5) {
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
						if (x[7] <= 2.5) {
							if (x[7] <= 0.5) {
								if (x[8] <= 3.0) {
									if (x[8] <= 1.5) {
										return 0.0f;
									}
									else {
										return 1.0f;
									}

								}
								else {
									if (x[8] <= 5.5) {
										return 0.0f;
									}
									else {
										return 1.0f;
									}

								}

							}
							else {
								if (x[3] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
									}
									else {
										if (x[8] <= 1.0) {
											return 1.0f;
										}
										else {
											if (x[8] <= 3.0) {
												return 1.0f;
											}
											else {
												if (x[8] <= 4.5) {
													return 1.0f;
												}
												else {
													if (x[8] <= 5.5) {
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
									if (x[4] <= 0.5) {
										if (x[7] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													if (x[8] <= 4.5) {
														return 1.0f;
													}
													else {
														if (x[8] <= 5.5) {
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
										if (x[7] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													if (x[8] <= 4.5) {
														return 1.0f;
													}
													else {
														if (x[8] <= 5.5) {
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

								}

							}

						}
						else {
							if (x[8] <= 3.5) {
								if (x[8] <= 1.5) {
									return 0.0f;
								}
								else {
									if (x[8] <= 2.5) {
										return 1.0f;
									}
									else {
										return 2.0f;
									}

								}

							}
							else {
								if (x[3] <= 0.5) {
									if (x[7] <= 3.5) {
										if (x[8] <= 5.0) {
											return 2.0f;
										}
										else {
											return 1.0f;
										}

									}
									else {
										if (x[7] <= 4.5) {
											if (x[8] <= 5.5) {
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

								}
								else {
									if (x[4] <= 0.5) {
										if (x[7] <= 3.5) {
											if (x[8] <= 5.0) {
												return 2.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[7] <= 4.5) {
												if (x[8] <= 5.5) {
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

									}
									else {
										if (x[7] <= 3.5) {
											if (x[8] <= 5.0) {
												return 2.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[7] <= 4.5) {
												if (x[8] <= 5.5) {
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

									}

								}

							}

						}

					}

				}

			}
			else {
				if (x[4] <= 0.5) {
					if (x[3] <= 0.5) {
						if (x[7] <= 2.5) {
							if (x[7] <= 0.5) {
								if (x[8] <= 5.5) {
									if (x[6] <= 0.5) {
										if (x[8] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 3.0) {
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
								else {
									return 1.0f;
								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
									}
									else {
										if (x[8] <= 4.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[8] <= 4.5) {
											if (x[8] <= 3.0) {
												return 1.0f;
											}
											else {
												return 0.0f;
											}

										}
										else {
											if (x[8] <= 5.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													if (x[8] <= 4.5) {
														return 1.0f;
													}
													else {
														if (x[8] <= 5.5) {
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

								}

							}

						}
						else {
							if (x[7] <= 3.5) {
								if (x[8] <= 2.5) {
									if (x[0] <= 0.5) {
										return 1.0f;
									}
									else {
										if (x[6] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.5) {
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
										if (x[6] <= 0.5) {
											return 0.0f;
										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[8] <= 5.0) {
												return 2.0f;
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
								if (x[0] <= 0.5) {
									if (x[7] <= 4.5) {
										if (x[8] <= 4.5) {
											return 3.0f;
										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[8] <= 3.0) {
											return 3.0f;
										}
										else {
											return 1.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[8] <= 4.5) {
											if (x[7] <= 4.5) {
												if (x[8] <= 3.0) {
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
											if (x[8] <= 5.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[8] <= 4.5) {
											if (x[7] <= 4.5) {
												if (x[8] <= 3.0) {
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
											if (x[8] <= 5.5) {
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

					}
					else {
						if (x[7] <= 2.5) {
							if (x[7] <= 0.5) {
								if (x[8] <= 5.5) {
									if (x[6] <= 0.5) {
										if (x[8] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 3.0) {
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
								else {
									return 1.0f;
								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
									}
									else {
										if (x[8] <= 4.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[8] <= 4.5) {
											if (x[8] <= 3.0) {
												return 1.0f;
											}
											else {
												return 0.0f;
											}

										}
										else {
											if (x[8] <= 5.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													if (x[8] <= 4.5) {
														return 1.0f;
													}
													else {
														if (x[8] <= 5.5) {
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

								}

							}

						}
						else {
							if (x[0] <= 0.5) {
								if (x[7] <= 3.5) {
									if (x[8] <= 2.5) {
										return 1.0f;
									}
									else {
										if (x[8] <= 5.0) {
											return 2.0f;
										}
										else {
											return 1.0f;
										}

									}

								}
								else {
									if (x[7] <= 4.5) {
										if (x[8] <= 4.5) {
											return 3.0f;
										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[7] <= 5.5) {
											return 3.0f;
										}
										else {
											if (x[8] <= 3.0) {
												return 3.0f;
											}
											else {
												return 1.0f;
											}

										}

									}

								}

							}
							else {
								if (x[7] <= 3.5) {
									if (x[8] <= 3.5) {
										if (x[6] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 2.5) {
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
										return 1.0f;
									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[8] <= 4.5) {
											if (x[7] <= 4.5) {
												if (x[8] <= 3.0) {
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
											if (x[8] <= 5.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[8] <= 4.5) {
											if (x[7] <= 4.5) {
												if (x[8] <= 3.0) {
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
											if (x[8] <= 5.5) {
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

					}

				}
				else {
					if (x[3] <= 0.5) {
						if (x[7] <= 2.5) {
							if (x[7] <= 0.5) {
								if (x[8] <= 5.5) {
									if (x[6] <= 0.5) {
										if (x[8] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 3.0) {
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
								else {
									return 1.0f;
								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
									}
									else {
										if (x[8] <= 4.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[8] <= 4.5) {
											if (x[8] <= 3.0) {
												return 1.0f;
											}
											else {
												return 0.0f;
											}

										}
										else {
											if (x[8] <= 5.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													if (x[8] <= 4.5) {
														return 1.0f;
													}
													else {
														if (x[8] <= 5.5) {
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

								}

							}

						}
						else {
							if (x[0] <= 0.5) {
								if (x[7] <= 4.5) {
									if (x[7] <= 3.5) {
										if (x[8] <= 2.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 5.0) {
												return 2.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[8] <= 4.5) {
											return 3.0f;
										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[8] <= 3.0) {
										return 3.0f;
									}
									else {
										return 1.0f;
									}

								}

							}
							else {
								if (x[6] <= 0.5) {
									if (x[7] <= 3.5) {
										if (x[8] <= 1.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 2.5) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.5) {
													return 0.0f;
												}
												else {
													return 1.0f;
												}

											}

										}

									}
									else {
										if (x[8] <= 4.5) {
											if (x[7] <= 4.5) {
												if (x[8] <= 3.0) {
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
											if (x[8] <= 5.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}

								}
								else {
									if (x[7] <= 3.5) {
										if (x[8] <= 1.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 2.5) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.5) {
													return 2.0f;
												}
												else {
													return 1.0f;
												}

											}

										}

									}
									else {
										if (x[8] <= 4.5) {
											if (x[7] <= 4.5) {
												if (x[8] <= 3.0) {
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
											if (x[8] <= 5.5) {
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

					}
					else {
						if (x[7] <= 2.5) {
							if (x[7] <= 0.5) {
								if (x[8] <= 5.5) {
									if (x[6] <= 0.5) {
										if (x[8] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 3.0) {
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
								else {
									return 1.0f;
								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
									}
									else {
										if (x[8] <= 4.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[8] <= 4.5) {
											if (x[8] <= 3.0) {
												return 1.0f;
											}
											else {
												return 0.0f;
											}

										}
										else {
											if (x[8] <= 5.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													if (x[8] <= 4.5) {
														return 1.0f;
													}
													else {
														if (x[8] <= 5.5) {
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

								}

							}

						}
						else {
							if (x[8] <= 3.5) {
								if (x[7] <= 3.5) {
									if (x[0] <= 0.5) {
										if (x[8] <= 2.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[6] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 2.5) {
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
								else {
									if (x[0] <= 0.5) {
										return 3.0f;
									}
									else {
										return 1.0f;
									}

								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 4.5) {
										if (x[7] <= 3.5) {
											if (x[8] <= 5.0) {
												return 2.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[8] <= 4.5) {
												return 3.0f;
											}
											else {
												return 2.0f;
											}

										}

									}
									else {
										if (x[7] <= 5.5) {
											return 3.0f;
										}
										else {
											return 1.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[8] <= 4.5) {
											if (x[7] <= 3.5) {
												return 1.0f;
											}
											else {
												if (x[7] <= 5.0) {
													return 0.0f;
												}
												else {
													return 1.0f;
												}

											}

										}
										else {
											if (x[8] <= 5.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[8] <= 4.5) {
											if (x[7] <= 3.5) {
												return 1.0f;
											}
											else {
												return 0.0f;
											}

										}
										else {
											if (x[8] <= 5.5) {
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

					}

				}

			}

		}
		else {
			if (x[4] <= 0.5) {
				if (x[1] <= 0.5) {
					if (x[3] <= 0.5) {
						if (x[7] <= 2.5) {
							if (x[7] <= 0.5) {
								if (x[8] <= 5.5) {
									if (x[6] <= 0.5) {
										if (x[8] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 3.0) {
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
								else {
									return 1.0f;
								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
									}
									else {
										if (x[8] <= 4.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[7] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													if (x[8] <= 4.5) {
														return 1.0f;
													}
													else {
														if (x[8] <= 5.5) {
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
										if (x[7] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													if (x[8] <= 4.5) {
														return 1.0f;
													}
													else {
														if (x[8] <= 5.5) {
															return 2.0f;
														}
														else {
															return 1.0f;
														}

													}

												}

											}

										}

									}

								}

							}

						}
						else {
							if (x[8] <= 3.5) {
								if (x[7] <= 3.5) {
									if (x[0] <= 0.5) {
										if (x[8] <= 2.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[6] <= 0.5) {
											if (x[8] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 2.5) {
														return 1.0f;
													}
													else {
														return 0.0f;
													}

												}

											}

										}
										else {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 2.5) {
													return 1.0f;
												}
												else {
													return 2.0f;
												}

											}

										}

									}

								}
								else {
									if (x[0] <= 0.5) {
										return 3.0f;
									}
									else {
										return 1.0f;
									}

								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 4.5) {
										if (x[7] <= 3.5) {
											if (x[8] <= 5.0) {
												return 2.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[8] <= 4.5) {
												return 3.0f;
											}
											else {
												return 2.0f;
											}

										}

									}
									else {
										if (x[7] <= 5.5) {
											return 3.0f;
										}
										else {
											return 1.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[8] <= 4.5) {
											if (x[7] <= 3.5) {
												return 1.0f;
											}
											else {
												if (x[7] <= 5.0) {
													return 0.0f;
												}
												else {
													return 1.0f;
												}

											}

										}
										else {
											if (x[8] <= 5.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[7] <= 3.5) {
											if (x[8] <= 5.0) {
												return 2.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[8] <= 4.5) {
												if (x[7] <= 5.0) {
													return 3.0f;
												}
												else {
													return 1.0f;
												}

											}
											else {
												if (x[8] <= 5.5) {
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

						}

					}
					else {
						if (x[7] <= 2.5) {
							if (x[7] <= 0.5) {
								if (x[8] <= 5.5) {
									if (x[6] <= 0.5) {
										if (x[8] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 3.0) {
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
								else {
									return 1.0f;
								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
									}
									else {
										if (x[8] <= 4.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[7] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													if (x[8] <= 4.5) {
														return 1.0f;
													}
													else {
														if (x[8] <= 5.5) {
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
										if (x[8] <= 4.5) {
											return 1.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
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
							if (x[0] <= 0.5) {
								if (x[7] <= 3.5) {
									if (x[8] <= 2.5) {
										return 1.0f;
									}
									else {
										if (x[8] <= 5.0) {
											return 2.0f;
										}
										else {
											return 1.0f;
										}

									}

								}
								else {
									if (x[7] <= 4.5) {
										if (x[8] <= 4.5) {
											return 3.0f;
										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[7] <= 5.5) {
											return 3.0f;
										}
										else {
											if (x[8] <= 3.0) {
												return 3.0f;
											}
											else {
												if (x[8] <= 5.0) {
													return 1.0f;
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
								if (x[6] <= 0.5) {
									if (x[7] <= 3.5) {
										if (x[8] <= 1.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 2.5) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.5) {
													return 0.0f;
												}
												else {
													return 1.0f;
												}

											}

										}

									}
									else {
										if (x[8] <= 4.5) {
											if (x[7] <= 4.5) {
												if (x[8] <= 3.0) {
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
											if (x[8] <= 5.5) {
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
										if (x[8] <= 1.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 2.5) {
												return 1.0f;
											}
											else {
												return 2.0f;
											}

										}

									}
									else {
										if (x[7] <= 3.5) {
											if (x[8] <= 5.0) {
												return 2.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[8] <= 4.5) {
												if (x[7] <= 5.0) {
													return 3.0f;
												}
												else {
													return 1.0f;
												}

											}
											else {
												if (x[8] <= 5.5) {
													return 2.0f;
												}
												else {
													return 1.0f;
												}

											}

										}

									}

								}

							}

						}

					}

				}
				else {
					if (x[3] <= 0.5) {
						if (x[7] <= 2.5) {
							if (x[7] <= 0.5) {
								if (x[8] <= 5.5) {
									if (x[6] <= 0.5) {
										if (x[8] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 3.0) {
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
								else {
									return 1.0f;
								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
									}
									else {
										if (x[8] <= 4.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[8] <= 4.5) {
											if (x[8] <= 3.0) {
												return 1.0f;
											}
											else {
												return 0.0f;
											}

										}
										else {
											if (x[8] <= 5.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													if (x[8] <= 4.5) {
														return 1.0f;
													}
													else {
														if (x[8] <= 5.5) {
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

								}

							}

						}
						else {
							if (x[0] <= 0.5) {
								if (x[7] <= 3.5) {
									if (x[8] <= 2.5) {
										return 1.0f;
									}
									else {
										if (x[8] <= 5.0) {
											return 2.0f;
										}
										else {
											return 1.0f;
										}

									}

								}
								else {
									if (x[7] <= 4.5) {
										if (x[8] <= 4.5) {
											return 3.0f;
										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[7] <= 5.5) {
											return 3.0f;
										}
										else {
											if (x[8] <= 3.0) {
												return 3.0f;
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
									if (x[7] <= 3.5) {
										if (x[8] <= 3.5) {
											return 0.0f;
										}
										else {
											return 1.0f;
										}

									}
									else {
										if (x[8] <= 4.5) {
											if (x[7] <= 4.5) {
												if (x[8] <= 3.0) {
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
											if (x[8] <= 5.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}

								}
								else {
									if (x[7] <= 3.5) {
										if (x[8] <= 1.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 2.5) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.5) {
													return 2.0f;
												}
												else {
													return 1.0f;
												}

											}

										}

									}
									else {
										if (x[8] <= 4.5) {
											if (x[7] <= 4.5) {
												if (x[8] <= 3.0) {
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
											if (x[8] <= 5.5) {
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

					}
					else {
						if (x[7] <= 2.5) {
							if (x[7] <= 0.5) {
								if (x[8] <= 5.5) {
									if (x[6] <= 0.5) {
										if (x[8] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 3.0) {
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
								else {
									return 1.0f;
								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
									}
									else {
										if (x[8] <= 4.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[8] <= 4.5) {
											if (x[8] <= 3.0) {
												return 1.0f;
											}
											else {
												return 0.0f;
											}

										}
										else {
											if (x[8] <= 5.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													if (x[8] <= 4.5) {
														return 1.0f;
													}
													else {
														if (x[8] <= 5.5) {
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

								}

							}

						}
						else {
							if (x[8] <= 3.5) {
								if (x[7] <= 3.5) {
									if (x[0] <= 0.5) {
										if (x[8] <= 2.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[8] <= 2.5) {
											if (x[6] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													return 1.0f;
												}

											}

										}
										else {
											if (x[6] <= 0.5) {
												return 0.0f;
											}
											else {
												return 2.0f;
											}

										}

									}

								}
								else {
									if (x[0] <= 0.5) {
										return 3.0f;
									}
									else {
										return 1.0f;
									}

								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 4.5) {
										if (x[7] <= 3.5) {
											if (x[8] <= 5.0) {
												return 2.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[8] <= 4.5) {
												return 3.0f;
											}
											else {
												return 2.0f;
											}

										}

									}
									else {
										if (x[8] <= 5.0) {
											return 1.0f;
										}
										else {
											return 3.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[8] <= 4.5) {
											if (x[7] <= 3.5) {
												return 1.0f;
											}
											else {
												if (x[7] <= 5.0) {
													return 0.0f;
												}
												else {
													return 1.0f;
												}

											}

										}
										else {
											if (x[8] <= 5.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[7] <= 3.5) {
											if (x[8] <= 5.0) {
												return 2.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[7] <= 4.5) {
												if (x[8] <= 5.5) {
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

									}

								}

							}

						}

					}

				}

			}
			else {
				if (x[7] <= 2.5) {
					if (x[7] <= 0.5) {
						if (x[8] <= 5.5) {
							if (x[1] <= 0.5) {
								if (x[6] <= 0.5) {
									if (x[8] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[8] <= 1.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 3.0) {
												return 1.0f;
											}
											else {
												return 0.0f;
											}

										}

									}

								}
								else {
									if (x[0] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[8] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 3.0) {
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
							else {
								if (x[3] <= 0.5) {
									if (x[6] <= 0.5) {
										if (x[8] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 3.0) {
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
								else {
									if (x[0] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[6] <= 0.5) {
											if (x[8] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 3.0) {
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

							}

						}
						else {
							if (x[0] <= 0.5) {
								return 1.0f;
							}
							else {
								if (x[1] <= 0.5) {
									return 1.0f;
								}
								else {
									if (x[3] <= 0.5) {
										return 1.0f;
									}
									else {
										if (x[6] <= 0.5) {
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
					else {
						if (x[8] <= 4.5) {
							if (x[8] <= 3.0) {
								if (x[7] <= 1.5) {
									if (x[8] <= 1.0) {
										if (x[1] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[3] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[6] <= 0.5) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[1] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[3] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[6] <= 0.5) {
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
									if (x[8] <= 1.0) {
										if (x[1] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[3] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[6] <= 0.5) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[1] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[3] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[6] <= 0.5) {
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
							else {
								if (x[6] <= 0.5) {
									if (x[1] <= 0.5) {
										return 1.0f;
									}
									else {
										return 0.0f;
									}

								}
								else {
									if (x[0] <= 0.5) {
										return 1.0f;
									}
									else {
										if (x[1] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[3] <= 0.5) {
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
						else {
							if (x[8] <= 5.5) {
								if (x[0] <= 0.5) {
									return 2.0f;
								}
								else {
									if (x[1] <= 0.5) {
										if (x[6] <= 0.5) {
											return 0.0f;
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
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
									}
									else {
										return 2.0f;
									}

								}
								else {
									if (x[1] <= 0.5) {
										if (x[6] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
											}
											else {
												return 2.0f;
											}

										}

									}
									else {
										if (x[7] <= 1.5) {
											if (x[3] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[6] <= 0.5) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}
										else {
											if (x[3] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[6] <= 0.5) {
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
				else {
					if (x[8] <= 3.5) {
						if (x[7] <= 3.5) {
							if (x[0] <= 0.5) {
								if (x[8] <= 2.5) {
									if (x[1] <= 0.5) {
										return 1.0f;
									}
									else {
										if (x[3] <= 0.5) {
											return 1.0f;
										}
										else {
											return 0.0f;
										}

									}

								}
								else {
									return 2.0f;
								}

							}
							else {
								if (x[1] <= 0.5) {
									if (x[6] <= 0.5) {
										if (x[8] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 2.5) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[8] <= 1.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 2.5) {
												return 1.0f;
											}
											else {
												return 2.0f;
											}

										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[3] <= 0.5) {
											if (x[8] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 2.5) {
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
									else {
										if (x[8] <= 2.5) {
											if (x[3] <= 0.5) {
												if (x[8] <= 1.5) {
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
											if (x[3] <= 0.5) {
												return 2.0f;
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
							if (x[0] <= 0.5) {
								return 3.0f;
							}
							else {
								if (x[7] <= 4.5) {
									if (x[1] <= 0.5) {
										return 1.0f;
									}
									else {
										if (x[3] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[6] <= 0.5) {
												return 1.0f;
											}
											else {
												return 0.0f;
											}

										}

									}

								}
								else {
									if (x[7] <= 5.5) {
										if (x[1] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[3] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[6] <= 0.5) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[1] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[3] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[6] <= 0.5) {
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
					else {
						if (x[0] <= 0.5) {
							if (x[7] <= 4.5) {
								if (x[7] <= 3.5) {
									if (x[8] <= 5.0) {
										return 2.0f;
									}
									else {
										if (x[1] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[3] <= 0.5) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}

									}

								}
								else {
									if (x[8] <= 4.5) {
										return 3.0f;
									}
									else {
										return 2.0f;
									}

								}

							}
							else {
								if (x[8] <= 5.0) {
									return 1.0f;
								}
								else {
									if (x[1] <= 0.5) {
										return 3.0f;
									}
									else {
										if (x[3] <= 0.5) {
											if (x[7] <= 5.5) {
												return 3.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											return 3.0f;
										}

									}

								}

							}

						}
						else {
							if (x[8] <= 4.5) {
								if (x[6] <= 0.5) {
									if (x[1] <= 0.5) {
										if (x[7] <= 3.5) {
											return 1.0f;
										}
										else {
											if (x[7] <= 5.0) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[3] <= 0.5) {
											if (x[7] <= 3.5) {
												return 1.0f;
											}
											else {
												if (x[7] <= 5.0) {
													return 0.0f;
												}
												else {
													return 1.0f;
												}

											}

										}
										else {
											if (x[7] <= 3.5) {
												return 1.0f;
											}
											else {
												if (x[7] <= 5.0) {
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
									if (x[1] <= 0.5) {
										if (x[7] <= 3.5) {
											return 2.0f;
										}
										else {
											if (x[7] <= 5.0) {
												return 3.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[3] <= 0.5) {
											if (x[7] <= 3.5) {
												return 1.0f;
											}
											else {
												if (x[7] <= 5.0) {
													return 0.0f;
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
								if (x[8] <= 5.5) {
									if (x[1] <= 0.5) {
										if (x[6] <= 0.5) {
											return 0.0f;
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
									if (x[7] <= 4.5) {
										if (x[7] <= 3.5) {
											if (x[1] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[3] <= 0.5) {
													return 1.0f;
												}
												else {
													if (x[6] <= 0.5) {
														return 1.0f;
													}
													else {
														return 0.0f;
													}

												}

											}

										}
										else {
											if (x[1] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[3] <= 0.5) {
													return 1.0f;
												}
												else {
													if (x[6] <= 0.5) {
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
										if (x[7] <= 5.5) {
											if (x[1] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[3] <= 0.5) {
													return 1.0f;
												}
												else {
													if (x[6] <= 0.5) {
														return 1.0f;
													}
													else {
														return 0.0f;
													}

												}

											}

										}
										else {
											if (x[1] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[3] <= 0.5) {
													return 1.0f;
												}
												else {
													if (x[6] <= 0.5) {
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

			}

		}

	}
	else {
		if (x[7] <= 9.5) {
			if (x[4] <= 0.5) {
				if (x[1] <= 0.5) {
					if (x[8] <= 4.5) {
						if (x[7] <= 8.5) {
							if (x[3] <= 0.5) {
								if (x[6] <= 0.5) {
									if (x[2] <= 0.5) {
										if (x[8] <= 3.0) {
											return 1.0f;
										}
										else {
											return 3.0f;
										}

									}
									else {
										if (x[7] <= 7.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 3.0) {
												return 1.0f;
											}
											else {
												return 0.0f;
											}

										}

									}

								}
								else {
									if (x[0] <= 0.5) {
										if (x[7] <= 7.5) {
											if (x[2] <= 0.5) {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[2] <= 0.5) {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[7] <= 7.5) {
											if (x[2] <= 0.5) {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[2] <= 0.5) {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
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
								if (x[7] <= 7.5) {
									if (x[0] <= 0.5) {
										if (x[2] <= 0.5) {
											if (x[8] <= 3.0) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}
										else {
											if (x[8] <= 3.0) {
												return 3.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[6] <= 0.5) {
											if (x[2] <= 0.5) {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[2] <= 0.5) {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 1.0f;
											}

										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[2] <= 0.5) {
											if (x[8] <= 3.0) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}
										else {
											if (x[8] <= 3.0) {
												return 1.0f;
											}
											else {
												return 0.0f;
											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[2] <= 0.5) {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[2] <= 0.5) {
												if (x[8] <= 3.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

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
							if (x[2] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[3] <= 0.5) {
										if (x[8] <= 2.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 3.5) {
												return 2.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[8] <= 2.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 3.5) {
												return 2.0f;
											}
											else {
												return 3.0f;
											}

										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[3] <= 0.5) {
											if (x[8] <= 2.5) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.5) {
													return 2.0f;
												}
												else {
													return 1.0f;
												}

											}

										}
										else {
											if (x[8] <= 2.5) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.5) {
													return 2.0f;
												}
												else {
													return 3.0f;
												}

											}

										}

									}
									else {
										if (x[3] <= 0.5) {
											if (x[8] <= 2.5) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.5) {
													return 2.0f;
												}
												else {
													return 1.0f;
												}

											}

										}
										else {
											if (x[8] <= 2.5) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.5) {
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
								if (x[3] <= 0.5) {
									if (x[0] <= 0.5) {
										if (x[8] <= 2.5) {
											return 1.0f;
										}
										else {
											if (x[8] <= 3.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[6] <= 0.5) {
											if (x[8] <= 2.5) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.5) {
													return 2.0f;
												}
												else {
													return 1.0f;
												}

											}

										}
										else {
											if (x[8] <= 2.5) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.5) {
													return 2.0f;
												}
												else {
													return 1.0f;
												}

											}

										}

									}

								}
								else {
									if (x[8] <= 2.5) {
										return 1.0f;
									}
									else {
										if (x[0] <= 0.5) {
											return 2.0f;
										}
										else {
											if (x[6] <= 0.5) {
												if (x[8] <= 3.5) {
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

								}

							}

						}

					}
					else {
						if (x[7] <= 7.5) {
							if (x[0] <= 0.5) {
								if (x[2] <= 0.5) {
									return 1.0f;
								}
								else {
									if (x[3] <= 0.5) {
										return 1.0f;
									}
									else {
										return 3.0f;
									}

								}

							}
							else {
								return 1.0f;
							}

						}
						else {
							if (x[7] <= 8.5) {
								if (x[2] <= 0.5) {
									if (x[3] <= 0.5) {
										if (x[0] <= 0.5) {
											return 2.0f;
										}
										else {
											if (x[6] <= 0.5) {
												if (x[8] <= 5.5) {
													return 0.0f;
												}
												else {
													return 2.0f;
												}

											}
											else {
												return 2.0f;
											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											return 2.0f;
										}
										else {
											if (x[6] <= 0.5) {
												if (x[8] <= 5.5) {
													return 0.0f;
												}
												else {
													return 2.0f;
												}

											}
											else {
												return 2.0f;
											}

										}

									}

								}
								else {
									if (x[3] <= 0.5) {
										if (x[0] <= 0.5) {
											return 2.0f;
										}
										else {
											if (x[6] <= 0.5) {
												if (x[8] <= 5.5) {
													return 0.0f;
												}
												else {
													return 2.0f;
												}

											}
											else {
												return 2.0f;
											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											return 2.0f;
										}
										else {
											if (x[6] <= 0.5) {
												if (x[8] <= 5.5) {
													return 0.0f;
												}
												else {
													return 2.0f;
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
								return 3.0f;
							}

						}

					}

				}
				else {
					if (x[2] <= 0.5) {
						if (x[3] <= 0.5) {
							if (x[7] <= 8.5) {
								if (x[8] <= 4.5) {
									if (x[8] <= 3.0) {
										return 1.0f;
									}
									else {
										return 3.0f;
									}

								}
								else {
									if (x[7] <= 7.5) {
										return 1.0f;
									}
									else {
										if (x[0] <= 0.5) {
											return 2.0f;
										}
										else {
											if (x[6] <= 0.5) {
												if (x[8] <= 5.5) {
													return 0.0f;
												}
												else {
													return 2.0f;
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
								if (x[8] <= 3.5) {
									return 0.0f;
								}
								else {
									if (x[8] <= 5.0) {
										return 1.0f;
									}
									else {
										return 3.0f;
									}

								}

							}

						}
						else {
							if (x[8] <= 3.5) {
								if (x[7] <= 8.5) {
									if (x[0] <= 0.5) {
										return 3.0f;
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
								if (x[8] <= 5.5) {
									if (x[8] <= 4.5) {
										return 3.0f;
									}
									else {
										if (x[6] <= 0.5) {
											return 0.0f;
										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[7] <= 7.5) {
										return 1.0f;
									}
									else {
										if (x[7] <= 8.5) {
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
						if (x[8] <= 4.5) {
							if (x[7] <= 8.5) {
								if (x[0] <= 0.5) {
									if (x[8] <= 3.0) {
										if (x[3] <= 0.5) {
											if (x[7] <= 7.5) {
												return 3.0f;
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
										return 1.0f;
									}

								}
								else {
									if (x[3] <= 0.5) {
										if (x[6] <= 0.5) {
											if (x[7] <= 7.5) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.0) {
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
										if (x[6] <= 0.5) {
											if (x[7] <= 7.5) {
												return 1.0f;
											}
											else {
												if (x[8] <= 3.0) {
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

								}

							}
							else {
								if (x[8] <= 3.5) {
									if (x[0] <= 0.5) {
										if (x[3] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 2.5) {
												return 3.0f;
											}
											else {
												return 0.0f;
											}

										}

									}
									else {
										if (x[3] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[6] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 2.5) {
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
									if (x[0] <= 0.5) {
										return 1.0f;
									}
									else {
										if (x[3] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[6] <= 0.5) {
												return 3.0f;
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
							if (x[3] <= 0.5) {
								if (x[7] <= 7.5) {
									return 1.0f;
								}
								else {
									if (x[7] <= 8.5) {
										if (x[0] <= 0.5) {
											return 2.0f;
										}
										else {
											if (x[6] <= 0.5) {
												if (x[8] <= 5.5) {
													return 0.0f;
												}
												else {
													return 2.0f;
												}

											}
											else {
												return 2.0f;
											}

										}

									}
									else {
										return 3.0f;
									}

								}

							}
							else {
								if (x[7] <= 7.5) {
									if (x[0] <= 0.5) {
										return 3.0f;
									}
									else {
										return 1.0f;
									}

								}
								else {
									if (x[7] <= 8.5) {
										if (x[0] <= 0.5) {
											return 2.0f;
										}
										else {
											if (x[6] <= 0.5) {
												if (x[8] <= 5.5) {
													return 0.0f;
												}
												else {
													return 2.0f;
												}

											}
											else {
												return 2.0f;
											}

										}

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
				if (x[2] <= 0.5) {
					if (x[8] <= 3.5) {
						if (x[7] <= 8.5) {
							if (x[7] <= 7.5) {
								if (x[0] <= 0.5) {
									if (x[1] <= 0.5) {
										return 1.0f;
									}
									else {
										if (x[3] <= 0.5) {
											return 1.0f;
										}
										else {
											return 3.0f;
										}

									}

								}
								else {
									return 1.0f;
								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[1] <= 0.5) {
										return 1.0f;
									}
									else {
										if (x[3] <= 0.5) {
											return 1.0f;
										}
										else {
											return 3.0f;
										}

									}

								}
								else {
									return 1.0f;
								}

							}

						}
						else {
							if (x[1] <= 0.5) {
								if (x[8] <= 2.5) {
									return 1.0f;
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
					else {
						if (x[8] <= 5.5) {
							if (x[8] <= 4.5) {
								if (x[0] <= 0.5) {
									if (x[1] <= 0.5) {
										return 3.0f;
									}
									else {
										if (x[3] <= 0.5) {
											if (x[7] <= 8.5) {
												return 3.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											return 3.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[1] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[3] <= 0.5) {
												if (x[7] <= 8.5) {
													return 3.0f;
												}
												else {
													return 1.0f;
												}

											}
											else {
												return 3.0f;
											}

										}

									}
									else {
										if (x[1] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[3] <= 0.5) {
												if (x[7] <= 8.5) {
													return 3.0f;
												}
												else {
													return 1.0f;
												}

											}
											else {
												return 3.0f;
											}

										}

									}

								}

							}
							else {
								if (x[6] <= 0.5) {
									return 0.0f;
								}
								else {
									return 2.0f;
								}

							}

						}
						else {
							if (x[7] <= 7.5) {
								return 1.0f;
							}
							else {
								if (x[7] <= 8.5) {
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
					if (x[7] <= 8.5) {
						if (x[8] <= 4.5) {
							if (x[8] <= 3.0) {
								if (x[0] <= 0.5) {
									if (x[1] <= 0.5) {
										return 1.0f;
									}
									else {
										if (x[3] <= 0.5) {
											if (x[7] <= 7.5) {
												return 3.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											return 3.0f;
										}

									}

								}
								else {
									if (x[7] <= 7.5) {
										if (x[1] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[3] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[6] <= 0.5) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[1] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[3] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[6] <= 0.5) {
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
							else {
								if (x[6] <= 0.5) {
									if (x[7] <= 7.5) {
										return 1.0f;
									}
									else {
										return 0.0f;
									}

								}
								else {
									if (x[7] <= 7.5) {
										if (x[0] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[1] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[3] <= 0.5) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[1] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[3] <= 0.5) {
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
						else {
							if (x[7] <= 7.5) {
								if (x[0] <= 0.5) {
									if (x[1] <= 0.5) {
										return 1.0f;
									}
									else {
										if (x[3] <= 0.5) {
											return 1.0f;
										}
										else {
											return 3.0f;
										}

									}

								}
								else {
									if (x[1] <= 0.5) {
										return 1.0f;
									}
									else {
										if (x[3] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[6] <= 0.5) {
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
								if (x[6] <= 0.5) {
									if (x[1] <= 0.5) {
										if (x[8] <= 5.5) {
											return 0.0f;
										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[3] <= 0.5) {
											if (x[8] <= 5.5) {
												return 0.0f;
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
								else {
									if (x[0] <= 0.5) {
										if (x[8] <= 5.5) {
											if (x[1] <= 0.5) {
												return 2.0f;
											}
											else {
												if (x[3] <= 0.5) {
													return 2.0f;
												}
												else {
													return 0.0f;
												}

											}

										}
										else {
											if (x[1] <= 0.5) {
												return 2.0f;
											}
											else {
												if (x[3] <= 0.5) {
													return 2.0f;
												}
												else {
													return 3.0f;
												}

											}

										}

									}
									else {
										if (x[8] <= 5.5) {
											if (x[1] <= 0.5) {
												return 2.0f;
											}
											else {
												if (x[3] <= 0.5) {
													return 2.0f;
												}
												else {
													return 0.0f;
												}

											}

										}
										else {
											if (x[1] <= 0.5) {
												return 2.0f;
											}
											else {
												if (x[3] <= 0.5) {
													return 2.0f;
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
					else {
						if (x[8] <= 3.5) {
							if (x[1] <= 0.5) {
								if (x[8] <= 2.5) {
									return 1.0f;
								}
								else {
									return 2.0f;
								}

							}
							else {
								if (x[8] <= 2.5) {
									if (x[0] <= 0.5) {
										if (x[3] <= 0.5) {
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
									if (x[0] <= 0.5) {
										if (x[3] <= 0.5) {
											return 0.0f;
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
							if (x[8] <= 5.0) {
								if (x[3] <= 0.5) {
									return 1.0f;
								}
								else {
									if (x[6] <= 0.5) {
										if (x[1] <= 0.5) {
											return 2.0f;
										}
										else {
											return 3.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											return 2.0f;
										}
										else {
											if (x[1] <= 0.5) {
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
								if (x[0] <= 0.5) {
									return 3.0f;
								}
								else {
									if (x[1] <= 0.5) {
										return 3.0f;
									}
									else {
										if (x[3] <= 0.5) {
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

			}

		}
		else {
			if (x[8] <= 3.5) {
				if (x[7] <= 11.5) {
					if (x[2] <= 0.5) {
						if (x[3] <= 0.5) {
							if (x[7] <= 10.5) {
								return 3.0f;
							}
							else {
								return 1.0f;
							}

						}
						else {
							if (x[0] <= 0.5) {
								if (x[4] <= 0.5) {
									if (x[1] <= 0.5) {
										if (x[7] <= 10.5) {
											return 1.0f;
										}
										else {
											return 3.0f;
										}

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
								if (x[7] <= 10.5) {
									if (x[1] <= 0.5) {
										if (x[4] <= 0.5) {
											if (x[6] <= 0.5) {
												return 3.0f;
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
										if (x[4] <= 0.5) {
											if (x[6] <= 0.5) {
												return 3.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											return 3.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[1] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[4] <= 0.5) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}

									}
									else {
										if (x[1] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[4] <= 0.5) {
												return 1.0f;
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
						if (x[4] <= 0.5) {
							if (x[1] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[3] <= 0.5) {
										return 3.0f;
									}
									else {
										if (x[7] <= 10.5) {
											return 1.0f;
										}
										else {
											return 3.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[3] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[7] <= 10.5) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}

									}
									else {
										if (x[3] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[7] <= 10.5) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}

									}

								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[3] <= 0.5) {
										if (x[7] <= 10.5) {
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
								else {
									if (x[6] <= 0.5) {
										if (x[3] <= 0.5) {
											if (x[7] <= 10.5) {
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
									else {
										if (x[3] <= 0.5) {
											if (x[7] <= 10.5) {
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

							}

						}
						else {
							if (x[3] <= 0.5) {
								if (x[7] <= 10.5) {
									return 3.0f;
								}
								else {
									return 1.0f;
								}

							}
							else {
								if (x[1] <= 0.5) {
									if (x[0] <= 0.5) {
										return 3.0f;
									}
									else {
										if (x[6] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[7] <= 10.5) {
												return 0.0f;
											}
											else {
												return 3.0f;
											}

										}

									}

								}
								else {
									if (x[7] <= 10.5) {
										if (x[0] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[6] <= 0.5) {
												return 3.0f;
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
											if (x[6] <= 0.5) {
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

				}
				else {
					if (x[1] <= 0.5) {
						if (x[8] <= 2.5) {
							return 3.0f;
						}
						else {
							if (x[0] <= 0.5) {
								if (x[4] <= 0.5) {
									return 0.0f;
								}
								else {
									return 2.0f;
								}

							}
							else {
								if (x[2] <= 0.5) {
									if (x[4] <= 0.5) {
										if (x[6] <= 0.5) {
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
								else {
									if (x[4] <= 0.5) {
										if (x[6] <= 0.5) {
											return 0.0f;
										}
										else {
											return 2.0f;
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
						if (x[2] <= 0.5) {
							if (x[0] <= 0.5) {
								if (x[3] <= 0.5) {
									return 0.0f;
								}
								else {
									if (x[4] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[8] <= 2.5) {
											return 3.0f;
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
							if (x[8] <= 2.5) {
								if (x[0] <= 0.5) {
									if (x[3] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[4] <= 0.5) {
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
									if (x[3] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[4] <= 0.5) {
											return 0.0f;
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

					}

				}

			}
			else {
				if (x[7] <= 11.5) {
					if (x[1] <= 0.5) {
						if (x[7] <= 10.5) {
							if (x[3] <= 0.5) {
								if (x[8] <= 5.0) {
									if (x[0] <= 0.5) {
										return 1.0f;
									}
									else {
										if (x[2] <= 0.5) {
											if (x[6] <= 0.5) {
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
									return 3.0f;
								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[2] <= 0.5) {
										if (x[4] <= 0.5) {
											if (x[8] <= 5.0) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}
										else {
											return 3.0f;
										}

									}
									else {
										if (x[4] <= 0.5) {
											if (x[8] <= 5.0) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}
										else {
											return 3.0f;
										}

									}

								}
								else {
									if (x[2] <= 0.5) {
										if (x[4] <= 0.5) {
											if (x[6] <= 0.5) {
												return 3.0f;
											}
											else {
												if (x[8] <= 5.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											return 3.0f;
										}

									}
									else {
										if (x[4] <= 0.5) {
											if (x[8] <= 5.0) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}
										else {
											return 3.0f;
										}

									}

								}

							}

						}
						else {
							if (x[8] <= 5.0) {
								if (x[4] <= 0.5) {
									return 1.0f;
								}
								else {
									if (x[0] <= 0.5) {
										if (x[2] <= 0.5) {
											return 3.0f;
										}
										else {
											return 1.0f;
										}

									}
									else {
										if (x[2] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[6] <= 0.5) {
												return 3.0f;
											}
											else {
												return 1.0f;
											}

										}

									}

								}

							}
							else {
								return 3.0f;
							}

						}

					}
					else {
						if (x[7] <= 10.5) {
							if (x[3] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[2] <= 0.5) {
										if (x[4] <= 0.5) {
											if (x[8] <= 5.0) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}
										else {
											return 3.0f;
										}

									}
									else {
										if (x[4] <= 0.5) {
											if (x[8] <= 5.0) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}
										else {
											return 3.0f;
										}

									}

								}
								else {
									if (x[2] <= 0.5) {
										if (x[4] <= 0.5) {
											if (x[6] <= 0.5) {
												return 3.0f;
											}
											else {
												if (x[8] <= 5.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											return 3.0f;
										}

									}
									else {
										if (x[4] <= 0.5) {
											if (x[8] <= 5.0) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}
										else {
											if (x[6] <= 0.5) {
												return 3.0f;
											}
											else {
												if (x[8] <= 5.0) {
													return 0.0f;
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
								if (x[0] <= 0.5) {
									if (x[2] <= 0.5) {
										if (x[4] <= 0.5) {
											if (x[8] <= 5.0) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}
										else {
											return 3.0f;
										}

									}
									else {
										if (x[4] <= 0.5) {
											if (x[8] <= 5.0) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}
										else {
											return 3.0f;
										}

									}

								}
								else {
									if (x[4] <= 0.5) {
										if (x[2] <= 0.5) {
											if (x[6] <= 0.5) {
												return 3.0f;
											}
											else {
												if (x[8] <= 5.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[8] <= 5.0) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}

									}
									else {
										if (x[2] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[6] <= 0.5) {
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
						else {
							if (x[2] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[3] <= 0.5) {
										return 3.0f;
									}
									else {
										if (x[4] <= 0.5) {
											if (x[8] <= 5.0) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}
										else {
											return 3.0f;
										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[3] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[4] <= 0.5) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}

									}
									else {
										if (x[3] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[4] <= 0.5) {
												if (x[8] <= 5.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 3.0f;
											}

										}

									}

								}

							}
							else {
								if (x[4] <= 0.5) {
									if (x[0] <= 0.5) {
										if (x[3] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[8] <= 5.0) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}

									}
									else {
										if (x[3] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[8] <= 5.0) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}

									}

								}
								else {
									if (x[8] <= 5.0) {
										if (x[0] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[3] <= 0.5) {
												return 3.0f;
											}
											else {
												if (x[6] <= 0.5) {
													return 3.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[3] <= 0.5) {
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

				}
				else {
					if (x[7] <= 12.5) {
						if (x[1] <= 0.5) {
							if (x[2] <= 0.5) {
								if (x[4] <= 0.5) {
									if (x[8] <= 5.0) {
										return 1.0f;
									}
									else {
										return 3.0f;
									}

								}
								else {
									if (x[8] <= 5.0) {
										return 2.0f;
									}
									else {
										return 3.0f;
									}

								}

							}
							else {
								if (x[4] <= 0.5) {
									if (x[8] <= 5.0) {
										return 1.0f;
									}
									else {
										return 3.0f;
									}

								}
								else {
									if (x[8] <= 5.0) {
										return 2.0f;
									}
									else {
										return 3.0f;
									}

								}

							}

						}
						else {
							if (x[4] <= 0.5) {
								if (x[8] <= 5.0) {
									return 1.0f;
								}
								else {
									return 3.0f;
								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[2] <= 0.5) {
										return 3.0f;
									}
									else {
										if (x[3] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[8] <= 5.0) {
												return 2.0f;
											}
											else {
												return 3.0f;
											}

										}

									}

								}
								else {
									if (x[8] <= 5.0) {
										if (x[2] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[3] <= 0.5) {
												return 3.0f;
											}
											else {
												if (x[6] <= 0.5) {
													return 3.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										if (x[2] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[3] <= 0.5) {
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
						if (x[2] <= 0.5) {
							if (x[0] <= 0.5) {
								if (x[1] <= 0.5) {
									if (x[3] <= 0.5) {
										return 3.0f;
									}
									else {
										if (x[4] <= 0.5) {
											if (x[7] <= 13.5) {
												if (x[8] <= 5.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 3.0f;
											}

										}
										else {
											return 3.0f;
										}

									}

								}
								else {
									if (x[3] <= 0.5) {
										if (x[4] <= 0.5) {
											if (x[7] <= 13.5) {
												if (x[8] <= 5.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 3.0f;
											}

										}
										else {
											return 3.0f;
										}

									}
									else {
										if (x[4] <= 0.5) {
											if (x[7] <= 13.5) {
												if (x[8] <= 5.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 3.0f;
											}

										}
										else {
											return 3.0f;
										}

									}

								}

							}
							else {
								if (x[6] <= 0.5) {
									if (x[1] <= 0.5) {
										if (x[4] <= 0.5) {
											if (x[7] <= 13.5) {
												return 1.0f;
											}
											else {
												return 3.0f;
											}

										}
										else {
											return 3.0f;
										}

									}
									else {
										if (x[3] <= 0.5) {
											if (x[4] <= 0.5) {
												if (x[7] <= 13.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 3.0f;
											}

										}
										else {
											if (x[4] <= 0.5) {
												if (x[7] <= 13.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 3.0f;
											}

										}

									}

								}
								else {
									if (x[1] <= 0.5) {
										if (x[3] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[4] <= 0.5) {
												if (x[7] <= 13.5) {
													if (x[8] <= 5.0) {
														return 1.0f;
													}
													else {
														return 3.0f;
													}

												}
												else {
													return 3.0f;
												}

											}
											else {
												return 3.0f;
											}

										}

									}
									else {
										if (x[3] <= 0.5) {
											if (x[4] <= 0.5) {
												if (x[7] <= 13.5) {
													if (x[8] <= 5.0) {
														return 1.0f;
													}
													else {
														return 3.0f;
													}

												}
												else {
													return 3.0f;
												}

											}
											else {
												return 3.0f;
											}

										}
										else {
											if (x[4] <= 0.5) {
												if (x[7] <= 13.5) {
													if (x[8] <= 5.0) {
														return 1.0f;
													}
													else {
														return 3.0f;
													}

												}
												else {
													return 3.0f;
												}

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
							if (x[4] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[1] <= 0.5) {
										if (x[3] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[7] <= 13.5) {
												if (x[8] <= 5.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 3.0f;
											}

										}

									}
									else {
										if (x[3] <= 0.5) {
											if (x[7] <= 13.5) {
												if (x[8] <= 5.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 3.0f;
											}

										}
										else {
											if (x[7] <= 13.5) {
												if (x[8] <= 5.0) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 3.0f;
											}

										}

									}

								}
								else {
									if (x[6] <= 0.5) {
										if (x[7] <= 13.5) {
											return 1.0f;
										}
										else {
											return 3.0f;
										}

									}
									else {
										if (x[1] <= 0.5) {
											if (x[3] <= 0.5) {
												return 3.0f;
											}
											else {
												if (x[7] <= 13.5) {
													if (x[8] <= 5.0) {
														return 1.0f;
													}
													else {
														return 3.0f;
													}

												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[3] <= 0.5) {
												if (x[7] <= 13.5) {
													if (x[8] <= 5.0) {
														return 1.0f;
													}
													else {
														return 3.0f;
													}

												}
												else {
													return 3.0f;
												}

											}
											else {
												if (x[7] <= 13.5) {
													if (x[8] <= 5.0) {
														return 1.0f;
													}
													else {
														return 3.0f;
													}

												}
												else {
													if (x[8] <= 5.0) {
														return 0.0f;
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
								if (x[7] <= 13.5) {
									if (x[8] <= 5.0) {
										if (x[0] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[1] <= 0.5) {
												return 3.0f;
											}
											else {
												if (x[3] <= 0.5) {
													return 3.0f;
												}
												else {
													if (x[6] <= 0.5) {
														return 3.0f;
													}
													else {
														return 0.0f;
													}

												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[1] <= 0.5) {
												return 3.0f;
											}
											else {
												if (x[3] <= 0.5) {
													return 3.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}

								}
								else {
									if (x[8] <= 5.0) {
										if (x[0] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[1] <= 0.5) {
												return 3.0f;
											}
											else {
												if (x[3] <= 0.5) {
													return 3.0f;
												}
												else {
													if (x[6] <= 0.5) {
														return 3.0f;
													}
													else {
														return 0.0f;
													}

												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[1] <= 0.5) {
												return 3.0f;
											}
											else {
												if (x[3] <= 0.5) {
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

					}

				}

			}

		}

	}

}