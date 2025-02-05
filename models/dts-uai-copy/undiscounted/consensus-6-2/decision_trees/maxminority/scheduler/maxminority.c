#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f,0.f,0.f,18.f,0.f,0.f,0.f,0.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[6] <= 17.5) {
		if (x[6] <= 12.5) {
			if (x[6] <= 9.5) {
				if (x[11] <= 0.5) {
					if (x[10] <= 0.5) {
						if (x[6] <= 7.5) {
							if (x[7] <= 1.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[8] <= 1.5) {
											if (x[1] <= 0.5) {
												if (x[8] <= 0.5) {
													if (x[9] <= 1.5) {
														return 1.0f;
													}
													else {
														return 17.0f;
													}

												}
												else {
													if (x[9] <= 1.5) {
														return 1.0f;
													}
													else {
														return 5.0f;
													}

												}

											}
											else {
												return 8.0f;
											}

										}
										else {
											return 4.0f;
										}

									}

								}
								else {
									return 2.0f;
								}

							}
							else {
								if (x[9] <= 0.5) {
									if (x[1] <= 0.5) {
										if (x[6] <= 6.5) {
											if (x[8] <= 0.5) {
												return 17.0f;
											}
											else {
												return 18.0f;
											}

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
									if (x[1] <= 0.5) {
										if (x[2] <= 0.5) {
											if (x[6] <= 6.5) {
												if (x[8] <= 0.5) {
													return 17.0f;
												}
												else {
													return 19.0f;
												}

											}
											else {
												return 3.0f;
											}

										}
										else {
											return 9.0f;
										}

									}
									else {
										return 8.0f;
									}

								}

							}

						}
						else {
							if (x[6] <= 8.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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

					}
					else {
						if (x[10] <= 1.5) {
							if (x[9] <= 0.5) {
								if (x[6] <= 7.5) {
									if (x[7] <= 1.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 1.0f;
												}
												else {
													return 4.0f;
												}

											}

										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[1] <= 0.5) {
											if (x[6] <= 6.5) {
												if (x[8] <= 0.5) {
													return 17.0f;
												}
												else {
													return 18.0f;
												}

											}
											else {
												return 3.0f;
											}

										}
										else {
											return 8.0f;
										}

									}

								}
								else {
									if (x[6] <= 8.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}
							else {
								if (x[6] <= 7.5) {
									if (x[7] <= 1.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													if (x[9] <= 1.5) {
														return 1.0f;
													}
													else {
														return 5.0f;
													}

												}
												else {
													return 4.0f;
												}

											}

										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[1] <= 0.5) {
											if (x[2] <= 0.5) {
												if (x[3] <= 0.5) {
													if (x[6] <= 6.5) {
														if (x[8] <= 0.5) {
															return 17.0f;
														}
														else {
															return 20.0f;
														}

													}
													else {
														return 3.0f;
													}

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
											return 8.0f;
										}

									}

								}
								else {
									if (x[6] <= 8.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}

						}
						else {
							if (x[9] <= 0.5) {
								if (x[6] <= 7.5) {
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[1] <= 0.5) {
												if (x[7] <= 1.5) {
													if (x[8] <= 0.5) {
														return 17.0f;
													}
													else {
														if (x[8] <= 1.5) {
															return 18.0f;
														}
														else {
															return 4.0f;
														}

													}

												}
												else {
													return 3.0f;
												}

											}
											else {
												return 8.0f;
											}

										}

									}
									else {
										return 2.0f;
									}

								}
								else {
									if (x[6] <= 8.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}
							else {
								if (x[6] <= 7.5) {
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[9] <= 1.5) {
												if (x[2] <= 0.5) {
													if (x[7] <= 1.5) {
														return 6.0f;
													}
													else {
														return 3.0f;
													}

												}
												else {
													return 9.0f;
												}

											}
											else {
												if (x[1] <= 0.5) {
													if (x[7] <= 1.5) {
														if (x[8] <= 0.5) {
															return 17.0f;
														}
														else {
															if (x[8] <= 1.5) {
																return 5.0f;
															}
															else {
																return 4.0f;
															}

														}

													}
													else {
														return 3.0f;
													}

												}
												else {
													return 8.0f;
												}

											}

										}

									}
									else {
										return 2.0f;
									}

								}
								else {
									if (x[6] <= 8.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}

						}

					}

				}
				else {
					if (x[11] <= 1.5) {
						if (x[6] <= 7.5) {
							if (x[7] <= 1.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[8] <= 1.5) {
											if (x[9] <= 1.5) {
												if (x[10] <= 1.5) {
													if (x[12] <= 1.0) {
														return 1.0f;
													}
													else {
														return 16.0f;
													}

												}
												else {
													return 6.0f;
												}

											}
											else {
												return 5.0f;
											}

										}
										else {
											return 4.0f;
										}

									}

								}
								else {
									return 2.0f;
								}

							}
							else {
								if (x[12] <= 0.5) {
									if (x[10] <= 0.5) {
										if (x[9] <= 0.5) {
											if (x[1] <= 0.5) {
												if (x[6] <= 6.5) {
													if (x[8] <= 0.5) {
														return 17.0f;
													}
													else {
														return 18.0f;
													}

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
											if (x[1] <= 0.5) {
												if (x[2] <= 0.5) {
													if (x[6] <= 6.5) {
														if (x[8] <= 0.5) {
															return 17.0f;
														}
														else {
															return 19.0f;
														}

													}
													else {
														return 3.0f;
													}

												}
												else {
													return 9.0f;
												}

											}
											else {
												return 8.0f;
											}

										}

									}
									else {
										if (x[9] <= 0.5) {
											if (x[1] <= 0.5) {
												if (x[6] <= 6.5) {
													if (x[8] <= 0.5) {
														return 17.0f;
													}
													else {
														return 18.0f;
													}

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
											if (x[1] <= 0.5) {
												if (x[2] <= 0.5) {
													if (x[3] <= 0.5) {
														if (x[4] <= 0.5) {
															if (x[6] <= 6.5) {
																if (x[8] <= 0.5) {
																	return 17.0f;
																}
																else {
																	return 21.0f;
																}

															}
															else {
																return 3.0f;
															}

														}
														else {
															return 11.0f;
														}

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
												return 8.0f;
											}

										}

									}

								}
								else {
									if (x[8] <= 2.5) {
										if (x[7] <= 2.5) {
											if (x[5] <= 0.5) {
												if (x[6] <= 6.5) {
													return 22.0f;
												}
												else {
													return 3.0f;
												}

											}
											else {
												return 23.0f;
											}

										}
										else {
											if (x[6] <= 5.5) {
												return 26.0f;
											}
											else {
												return 12.0f;
											}

										}

									}
									else {
										if (x[6] <= 3.5) {
											if (x[10] <= 2.5) {
												return 30.0f;
											}
											else {
												return 15.0f;
											}

										}
										else {
											if (x[6] <= 4.5) {
												if (x[9] <= 2.5) {
													return 28.0f;
												}
												else {
													return 14.0f;
												}

											}
											else {
												return 13.0f;
											}

										}

									}

								}

							}

						}
						else {
							if (x[6] <= 8.5) {
								if (x[10] <= 0.5) {
									if (x[9] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
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
								if (x[10] <= 0.5) {
									if (x[9] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
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

						}

					}
					else {
						if (x[10] <= 1.5) {
							if (x[6] <= 7.5) {
								if (x[9] <= 0.5) {
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[1] <= 0.5) {
												if (x[7] <= 1.5) {
													if (x[8] <= 0.5) {
														return 17.0f;
													}
													else {
														if (x[8] <= 1.5) {
															return 18.0f;
														}
														else {
															return 4.0f;
														}

													}

												}
												else {
													return 3.0f;
												}

											}
											else {
												return 8.0f;
											}

										}

									}
									else {
										return 2.0f;
									}

								}
								else {
									if (x[9] <= 1.5) {
										if (x[10] <= 0.5) {
											if (x[0] <= 0.5) {
												if (x[2] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 19.0f;
														}
														else {
															return 3.0f;
														}

													}

												}
												else {
													return 9.0f;
												}

											}
											else {
												return 2.0f;
											}

										}
										else {
											if (x[0] <= 0.5) {
												if (x[3] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 7.0f;
														}
														else {
															return 3.0f;
														}

													}

												}
												else {
													return 10.0f;
												}

											}
											else {
												return 2.0f;
											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[1] <= 0.5) {
													if (x[7] <= 1.5) {
														if (x[8] <= 0.5) {
															return 17.0f;
														}
														else {
															if (x[8] <= 1.5) {
																return 5.0f;
															}
															else {
																return 4.0f;
															}

														}

													}
													else {
														return 3.0f;
													}

												}
												else {
													return 8.0f;
												}

											}

										}
										else {
											return 2.0f;
										}

									}

								}

							}
							else {
								if (x[6] <= 8.5) {
									if (x[9] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[9] <= 1.5) {
											if (x[10] <= 0.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[0] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 1.5) {
														return 1.0f;
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

								}
								else {
									if (x[9] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[9] <= 1.5) {
											if (x[10] <= 0.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[0] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 1.5) {
														return 1.0f;
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

								}

							}

						}
						else {
							if (x[9] <= 1.5) {
								if (x[6] <= 7.5) {
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[9] <= 0.5) {
												if (x[1] <= 0.5) {
													if (x[7] <= 1.5) {
														if (x[8] <= 0.5) {
															return 17.0f;
														}
														else {
															if (x[8] <= 1.5) {
																return 18.0f;
															}
															else {
																return 4.0f;
															}

														}

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
												if (x[2] <= 0.5) {
													if (x[7] <= 1.5) {
														return 6.0f;
													}
													else {
														return 3.0f;
													}

												}
												else {
													return 9.0f;
												}

											}

										}

									}
									else {
										return 2.0f;
									}

								}
								else {
									if (x[6] <= 8.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}
							else {
								if (x[6] <= 7.5) {
									if (x[7] <= 1.5) {
										if (x[0] <= 0.5) {
											if (x[1] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[8] <= 0.5) {
														return 17.0f;
													}
													else {
														if (x[8] <= 1.5) {
															return 5.0f;
														}
														else {
															return 4.0f;
														}

													}

												}

											}
											else {
												return 8.0f;
											}

										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[6] <= 1.5) {
											if (x[12] <= 2.5) {
												return 34.0f;
											}
											else {
												return 36.0f;
											}

										}
										else {
											if (x[6] <= 4.5) {
												if (x[11] <= 2.5) {
													return 32.0f;
												}
												else {
													return 24.0f;
												}

											}
											else {
												return 3.0f;
											}

										}

									}

								}
								else {
									if (x[6] <= 8.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}

						}

					}

				}

			}
			else {
				if (x[10] <= 0.5) {
					if (x[9] <= 0.5) {
						if (x[0] <= 0.5) {
							if (x[7] <= 0.5) {
								return 0.0f;
							}
							else {
								if (x[7] <= 1.5) {
									return 1.0f;
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
					else {
						if (x[9] <= 1.5) {
							if (x[11] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							if (x[11] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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

					}

				}
				else {
					if (x[10] <= 1.5) {
						if (x[11] <= 0.5) {
							if (x[9] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							if (x[0] <= 0.5) {
								if (x[7] <= 0.5) {
									return 0.0f;
								}
								else {
									if (x[7] <= 1.5) {
										return 1.0f;
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
						if (x[11] <= 0.5) {
							if (x[9] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							if (x[9] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[9] <= 1.5) {
									if (x[11] <= 1.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
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

						}

					}

				}

			}

		}
		else {
			if (x[6] <= 15.5) {
				if (x[10] <= 0.5) {
					if (x[9] <= 0.5) {
						if (x[6] <= 14.5) {
							if (x[6] <= 13.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							if (x[7] <= 0.5) {
								if (x[4] <= 0.5) {
									return 0.0f;
								}
								else {
									return 11.0f;
								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
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
					else {
						if (x[9] <= 1.5) {
							if (x[11] <= 0.5) {
								if (x[6] <= 14.5) {
									if (x[6] <= 13.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[7] <= 0.5) {
										if (x[2] <= 0.5) {
											return 0.0f;
										}
										else {
											return 9.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 1.5) {
												return 1.0f;
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
							else {
								if (x[6] <= 14.5) {
									if (x[6] <= 13.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[7] <= 0.5) {
										if (x[2] <= 0.5) {
											return 0.0f;
										}
										else {
											return 9.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 1.5) {
												return 1.0f;
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
						else {
							if (x[11] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[6] <= 14.5) {
									if (x[6] <= 13.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[7] <= 0.5) {
											if (x[4] <= 0.5) {
												return 0.0f;
											}
											else {
												return 11.0f;
											}

										}
										else {
											if (x[0] <= 0.5) {
												if (x[7] <= 1.5) {
													return 1.0f;
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
								else {
									if (x[11] <= 1.5) {
										if (x[4] <= 0.5) {
											if (x[0] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 1.5) {
														return 1.0f;
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
										else {
											if (x[7] <= 0.5) {
												if (x[8] <= 1.0) {
													return 11.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 1.5) {
														return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}

						}

					}

				}
				else {
					if (x[10] <= 1.5) {
						if (x[11] <= 0.5) {
							if (x[9] <= 0.5) {
								if (x[6] <= 14.5) {
									if (x[6] <= 13.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[7] <= 0.5) {
										if (x[3] <= 0.5) {
											return 0.0f;
										}
										else {
											return 10.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 1.5) {
												return 1.0f;
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
							else {
								if (x[6] <= 14.5) {
									if (x[6] <= 13.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[7] <= 0.5) {
											if (x[3] <= 0.5) {
												return 0.0f;
											}
											else {
												return 10.0f;
											}

										}
										else {
											if (x[0] <= 0.5) {
												if (x[7] <= 1.5) {
													return 1.0f;
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
								else {
									if (x[7] <= 0.5) {
										if (x[2] <= 0.5) {
											if (x[3] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.0) {
													return 10.0f;
												}
												else {
													return 0.0f;
												}

											}

										}
										else {
											return 9.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 1.5) {
												return 1.0f;
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
						else {
							if (x[6] <= 14.5) {
								if (x[6] <= 13.5) {
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
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
								else {
									if (x[7] <= 0.5) {
										if (x[3] <= 0.5) {
											return 0.0f;
										}
										else {
											return 10.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 1.5) {
												return 1.0f;
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
							else {
								if (x[7] <= 0.5) {
									if (x[2] <= 0.5) {
										if (x[3] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 10.0f;
											}
											else {
												if (x[9] <= 1.0) {
													return 10.0f;
												}
												else {
													return 0.0f;
												}

											}

										}

									}
									else {
										return 9.0f;
									}

								}
								else {
									if (x[0] <= 0.5) {
										if (x[7] <= 1.5) {
											return 1.0f;
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
					else {
						if (x[9] <= 1.5) {
							if (x[11] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[6] <= 14.5) {
									if (x[6] <= 13.5) {
										if (x[9] <= 0.5) {
											if (x[0] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 1.5) {
														return 1.0f;
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
										else {
											if (x[11] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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

									}
									else {
										if (x[7] <= 0.5) {
											if (x[4] <= 0.5) {
												return 0.0f;
											}
											else {
												return 11.0f;
											}

										}
										else {
											if (x[0] <= 0.5) {
												if (x[7] <= 1.5) {
													return 1.0f;
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
								else {
									if (x[7] <= 0.5) {
										if (x[4] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 11.0f;
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
						else {
							if (x[11] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[7] <= 0.5) {
									if (x[4] <= 0.5) {
										if (x[6] <= 13.5) {
											return 0.0f;
										}
										else {
											if (x[6] <= 14.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 0.0f;
												}
												else {
													return 4.0f;
												}

											}

										}

									}
									else {
										if (x[6] <= 13.5) {
											return 11.0f;
										}
										else {
											if (x[6] <= 14.5) {
												if (x[8] <= 1.0) {
													return 11.0f;
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
										if (x[7] <= 1.5) {
											return 1.0f;
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
				if (x[6] <= 16.5) {
					if (x[10] <= 0.5) {
						if (x[7] <= 0.5) {
							if (x[1] <= 0.5) {
								if (x[2] <= 0.5) {
									if (x[4] <= 0.5) {
										if (x[8] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[9] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[11] <= 1.5) {
														return 0.0f;
													}
													else {
														return 4.0f;
													}

												}

											}

										}

									}
									else {
										if (x[8] <= 1.0) {
											if (x[9] <= 1.0) {
												return 11.0f;
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
									if (x[8] <= 1.0) {
										return 9.0f;
									}
									else {
										return 0.0f;
									}

								}

							}
							else {
								return 8.0f;
							}

						}
						else {
							if (x[0] <= 0.5) {
								if (x[7] <= 1.5) {
									return 1.0f;
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
						if (x[11] <= 0.5) {
							if (x[9] <= 0.5) {
								if (x[7] <= 0.5) {
									if (x[1] <= 0.5) {
										if (x[3] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.0) {
												return 10.0f;
											}
											else {
												return 0.0f;
											}

										}

									}
									else {
										return 8.0f;
									}

								}
								else {
									if (x[0] <= 0.5) {
										if (x[7] <= 1.5) {
											return 1.0f;
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
								if (x[9] <= 1.5) {
									if (x[7] <= 0.5) {
										if (x[1] <= 0.5) {
											if (x[2] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[8] <= 1.0) {
													return 9.0f;
												}
												else {
													return 0.0f;
												}

											}

										}
										else {
											return 8.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 1.5) {
												return 1.0f;
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
									if (x[10] <= 1.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[7] <= 0.5) {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												return 4.0f;
											}

										}
										else {
											if (x[0] <= 0.5) {
												if (x[7] <= 1.5) {
													return 1.0f;
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
						else {
							if (x[7] <= 0.5) {
								if (x[3] <= 0.5) {
									if (x[8] <= 1.5) {
										if (x[8] <= 0.5) {
											if (x[4] <= 0.5) {
												if (x[9] <= 1.5) {
													return 0.0f;
												}
												else {
													return 5.0f;
												}

											}
											else {
												return 0.0f;
											}

										}
										else {
											if (x[9] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[9] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[10] <= 1.5) {
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
										if (x[4] <= 0.5) {
											if (x[10] <= 1.5) {
												return 0.0f;
											}
											else {
												return 4.0f;
											}

										}
										else {
											if (x[9] <= 1.0) {
												return 0.0f;
											}
											else {
												return 4.0f;
											}

										}

									}

								}
								else {
									if (x[1] <= 0.5) {
										if (x[2] <= 0.5) {
											if (x[8] <= 1.0) {
												if (x[9] <= 1.0) {
													return 10.0f;
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
											if (x[8] <= 1.0) {
												return 9.0f;
											}
											else {
												return 0.0f;
											}

										}

									}
									else {
										return 8.0f;
									}

								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
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
				else {
					if (x[10] <= 0.5) {
						if (x[9] <= 0.5) {
							if (x[7] <= 0.5) {
								if (x[1] <= 0.5) {
									if (x[4] <= 0.5) {
										if (x[8] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[11] <= 1.5) {
													return 0.0f;
												}
												else {
													return 4.0f;
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
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
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
							if (x[11] <= 0.5) {
								if (x[2] <= 0.5) {
									if (x[9] <= 1.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[7] <= 0.5) {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												return 4.0f;
											}

										}
										else {
											if (x[0] <= 0.5) {
												if (x[7] <= 1.5) {
													return 1.0f;
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
								else {
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
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
								if (x[4] <= 0.5) {
									if (x[7] <= 0.5) {
										if (x[8] <= 0.5) {
											if (x[9] <= 1.5) {
												return 0.0f;
											}
											else {
												return 5.0f;
											}

										}
										else {
											if (x[8] <= 1.5) {
												if (x[9] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[11] <= 1.5) {
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
										if (x[0] <= 0.5) {
											if (x[7] <= 1.5) {
												return 1.0f;
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
									if (x[8] <= 0.5) {
										if (x[2] <= 0.5) {
											if (x[0] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 1.5) {
														return 1.0f;
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
										else {
											if (x[0] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 1.5) {
														return 1.0f;
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
										if (x[1] <= 0.5) {
											if (x[7] <= 0.5) {
												if (x[2] <= 0.5) {
													return 4.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 1.5) {
														return 1.0f;
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
											if (x[0] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 1.5) {
														return 1.0f;
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

								}

							}

						}

					}
					else {
						if (x[11] <= 0.5) {
							if (x[9] <= 0.5) {
								if (x[3] <= 0.5) {
									if (x[10] <= 1.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[7] <= 0.5) {
											if (x[8] <= 1.5) {
												return 0.0f;
											}
											else {
												return 4.0f;
											}

										}
										else {
											if (x[0] <= 0.5) {
												if (x[7] <= 1.5) {
													return 1.0f;
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
								else {
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
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
								if (x[3] <= 0.5) {
									if (x[7] <= 0.5) {
										if (x[8] <= 0.5) {
											if (x[9] <= 1.5) {
												return 0.0f;
											}
											else {
												return 5.0f;
											}

										}
										else {
											if (x[8] <= 1.5) {
												if (x[9] <= 1.5) {
													return 0.0f;
												}
												else {
													if (x[10] <= 1.5) {
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
										if (x[0] <= 0.5) {
											if (x[7] <= 1.5) {
												return 1.0f;
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
									if (x[8] <= 0.5) {
										if (x[2] <= 0.5) {
											if (x[0] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 1.5) {
														return 1.0f;
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
										else {
											if (x[0] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 1.5) {
														return 1.0f;
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
										if (x[1] <= 0.5) {
											if (x[7] <= 0.5) {
												if (x[2] <= 0.5) {
													return 4.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 1.5) {
														return 1.0f;
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
											if (x[0] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 1.5) {
														return 1.0f;
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

								}

							}

						}
						else {
							if (x[4] <= 0.5) {
								if (x[7] <= 0.5) {
									if (x[10] <= 1.5) {
										return 0.0f;
									}
									else {
										if (x[11] <= 1.5) {
											return 0.0f;
										}
										else {
											return 6.0f;
										}

									}

								}
								else {
									if (x[0] <= 0.5) {
										if (x[7] <= 1.5) {
											return 1.0f;
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
								if (x[8] <= 0.5) {
									if (x[9] <= 0.5) {
										if (x[3] <= 0.5) {
											if (x[0] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 1.5) {
														return 1.0f;
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
										else {
											if (x[0] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 1.5) {
														return 1.0f;
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
										if (x[2] <= 0.5) {
											if (x[7] <= 0.5) {
												if (x[3] <= 0.5) {
													return 5.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 1.5) {
														return 1.0f;
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
											if (x[0] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 1.5) {
														return 1.0f;
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

								}
								else {
									if (x[9] <= 0.5) {
										if (x[1] <= 0.5) {
											if (x[7] <= 0.5) {
												if (x[3] <= 0.5) {
													return 4.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 1.5) {
														return 1.0f;
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
											if (x[0] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 1.5) {
														return 1.0f;
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
										if (x[1] <= 0.5) {
											if (x[7] <= 0.5) {
												if (x[2] <= 0.5) {
													return 4.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 1.5) {
														return 1.0f;
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
											if (x[0] <= 0.5) {
												if (x[7] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[7] <= 1.5) {
														return 1.0f;
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

								}

							}

						}

					}

				}

			}

		}

	}
	else {
		if (x[6] <= 23.5) {
			if (x[6] <= 20.5) {
				if (x[10] <= 0.5) {
					if (x[7] <= 0.5) {
						if (x[6] <= 18.5) {
							if (x[8] <= 1.5) {
								if (x[9] <= 1.5) {
									if (x[11] <= 1.5) {
										return 0.0f;
									}
									else {
										return 7.0f;
									}

								}
								else {
									return 5.0f;
								}

							}
							else {
								return 4.0f;
							}

						}
						else {
							if (x[6] <= 19.5) {
								if (x[8] <= 1.5) {
									if (x[1] <= 0.5) {
										if (x[2] <= 0.5) {
											if (x[4] <= 0.5) {
												if (x[8] <= 0.5) {
													if (x[9] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[11] <= 1.5) {
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
											else {
												return 0.0f;
											}

										}
										else {
											return 0.0f;
										}

									}
									else {
										if (x[2] <= 0.5) {
											if (x[4] <= 0.5) {
												if (x[9] <= 1.0) {
													return 0.0f;
												}
												else {
													if (x[11] <= 1.0) {
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
										else {
											return 0.0f;
										}

									}

								}
								else {
									if (x[9] <= 1.5) {
										if (x[11] <= 1.5) {
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

							}
							else {
								if (x[8] <= 0.5) {
									if (x[9] <= 0.5) {
										if (x[4] <= 0.5) {
											if (x[11] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[11] <= 1.5) {
													return 15.0f;
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
										if (x[11] <= 0.5) {
											if (x[2] <= 0.5) {
												if (x[9] <= 1.5) {
													return 13.0f;
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
											if (x[2] <= 0.5) {
												if (x[9] <= 1.5) {
													return 13.0f;
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
									if (x[9] <= 0.5) {
										if (x[11] <= 0.5) {
											if (x[1] <= 0.5) {
												if (x[8] <= 1.5) {
													return 12.0f;
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
											if (x[1] <= 0.5) {
												if (x[8] <= 1.5) {
													return 12.0f;
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
										if (x[8] <= 1.5) {
											if (x[1] <= 0.5) {
												return 12.0f;
											}
											else {
												return 0.0f;
											}

										}
										else {
											if (x[11] <= 1.5) {
												return 0.0f;
											}
											else {
												return 4.0f;
											}

										}

									}

								}

							}

						}

					}
					else {
						if (x[0] <= 0.5) {
							if (x[7] <= 1.5) {
								return 1.0f;
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
					if (x[11] <= 0.5) {
						if (x[9] <= 0.5) {
							if (x[7] <= 0.5) {
								if (x[10] <= 1.5) {
									if (x[6] <= 18.5) {
										if (x[8] <= 1.5) {
											return 0.0f;
										}
										else {
											return 4.0f;
										}

									}
									else {
										if (x[8] <= 0.5) {
											if (x[3] <= 0.5) {
												if (x[6] <= 19.5) {
													return 0.0f;
												}
												else {
													return 14.0f;
												}

											}
											else {
												return 0.0f;
											}

										}
										else {
											if (x[1] <= 0.5) {
												if (x[3] <= 0.5) {
													if (x[6] <= 19.5) {
														return 0.0f;
													}
													else {
														if (x[8] <= 1.5) {
															return 12.0f;
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

									}

								}
								else {
									if (x[6] <= 18.5) {
										return 6.0f;
									}
									else {
										if (x[1] <= 0.5) {
											if (x[6] <= 19.5) {
												if (x[8] <= 1.0) {
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
											return 0.0f;
										}

									}

								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
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
							if (x[7] <= 0.5) {
								if (x[6] <= 18.5) {
									if (x[2] <= 0.5) {
										if (x[9] <= 1.5) {
											if (x[8] <= 1.5) {
												if (x[10] <= 1.5) {
													return 0.0f;
												}
												else {
													return 6.0f;
												}

											}
											else {
												return 4.0f;
											}

										}
										else {
											return 5.0f;
										}

									}
									else {
										if (x[1] <= 0.5) {
											if (x[8] <= 1.0) {
												return 0.0f;
											}
											else {
												return 4.0f;
											}

										}
										else {
											if (x[3] <= 0.5) {
												return 6.0f;
											}
											else {
												return 0.0f;
											}

										}

									}

								}
								else {
									if (x[6] <= 19.5) {
										if (x[10] <= 1.5) {
											if (x[1] <= 0.5) {
												if (x[2] <= 0.5) {
													if (x[8] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[9] <= 1.5) {
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
										else {
											if (x[2] <= 0.5) {
												return 5.0f;
											}
											else {
												return 0.0f;
											}

										}

									}
									else {
										if (x[8] <= 0.5) {
											if (x[2] <= 0.5) {
												if (x[9] <= 1.5) {
													return 13.0f;
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
											if (x[8] <= 1.5) {
												if (x[1] <= 0.5) {
													return 12.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[10] <= 1.5) {
													return 0.0f;
												}
												else {
													return 4.0f;
												}

											}

										}

									}

								}

							}
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 1.5) {
										return 1.0f;
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
					else {
						if (x[7] <= 0.5) {
							if (x[6] <= 18.5) {
								if (x[4] <= 0.5) {
									if (x[8] <= 0.5) {
										if (x[9] <= 0.5) {
											if (x[10] <= 1.5) {
												return 0.0f;
											}
											else {
												return 6.0f;
											}

										}
										else {
											if (x[9] <= 1.5) {
												return 0.0f;
											}
											else {
												return 5.0f;
											}

										}

									}
									else {
										if (x[8] <= 1.5) {
											if (x[11] <= 1.5) {
												if (x[9] <= 1.5) {
													if (x[10] <= 1.5) {
														if (x[12] <= 1.0) {
															return 0.0f;
														}
														else {
															return 16.0f;
														}

													}
													else {
														return 6.0f;
													}

												}
												else {
													return 5.0f;
												}

											}
											else {
												return 7.0f;
											}

										}
										else {
											return 4.0f;
										}

									}

								}
								else {
									if (x[1] <= 0.5) {
										if (x[8] <= 1.0) {
											if (x[3] <= 0.5) {
												return 6.0f;
											}
											else {
												if (x[9] <= 1.5) {
													return 0.0f;
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
									else {
										if (x[2] <= 0.5) {
											if (x[9] <= 1.0) {
												return 0.0f;
											}
											else {
												return 5.0f;
											}

										}
										else {
											if (x[3] <= 0.5) {
												return 6.0f;
											}
											else {
												if (x[12] <= 1.0) {
													return 0.0f;
												}
												else {
													return 16.0f;
												}

											}

										}

									}

								}

							}
							else {
								if (x[6] <= 19.5) {
									if (x[9] <= 0.5) {
										if (x[11] <= 1.5) {
											if (x[1] <= 0.5) {
												if (x[3] <= 0.5) {
													if (x[8] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[10] <= 1.5) {
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
										else {
											return 6.0f;
										}

									}
									else {
										if (x[1] <= 0.5) {
											if (x[8] <= 0.5) {
												if (x[10] <= 1.5) {
													return 0.0f;
												}
												else {
													return 5.0f;
												}

											}
											else {
												if (x[9] <= 1.5) {
													return 0.0f;
												}
												else {
													return 4.0f;
												}

											}

										}
										else {
											if (x[2] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[3] <= 0.5) {
													if (x[4] <= 0.5) {
														return 6.0f;
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
								else {
									if (x[10] <= 1.5) {
										if (x[8] <= 0.5) {
											if (x[9] <= 0.5) {
												if (x[3] <= 0.5) {
													return 14.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[2] <= 0.5) {
													if (x[9] <= 1.5) {
														return 13.0f;
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
											if (x[9] <= 0.5) {
												if (x[1] <= 0.5) {
													if (x[8] <= 1.5) {
														return 12.0f;
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
												if (x[1] <= 0.5) {
													if (x[8] <= 1.5) {
														return 12.0f;
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
										if (x[8] <= 1.5) {
											if (x[1] <= 0.5) {
												if (x[9] <= 1.0) {
													return 0.0f;
												}
												else {
													if (x[11] <= 1.5) {
														return 0.0f;
													}
													else {
														return 5.0f;
													}

												}

											}
											else {
												if (x[9] <= 1.5) {
													return 0.0f;
												}
												else {
													return 5.0f;
												}

											}

										}
										else {
											if (x[9] <= 1.0) {
												if (x[11] <= 1.5) {
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

									}

								}

							}

						}
						else {
							if (x[0] <= 0.5) {
								if (x[7] <= 1.5) {
									return 1.0f;
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
			else {
				if (x[1] <= 0.5) {
					if (x[8] <= 1.0) {
						if (x[9] <= 0.5) {
							if (x[10] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[3] <= 0.5) {
									if (x[11] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[6] <= 21.5) {
											if (x[7] <= 0.5) {
												if (x[11] <= 1.5) {
													return 15.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 1.5) {
														return 1.0f;
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
											if (x[6] <= 22.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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

									}

								}
								else {
									if (x[4] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}

						}
						else {
							if (x[10] <= 0.5) {
								if (x[2] <= 0.5) {
									if (x[11] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[6] <= 21.5) {
											if (x[7] <= 0.5) {
												if (x[11] <= 1.5) {
													return 15.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 1.5) {
														return 1.0f;
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
											if (x[6] <= 22.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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

									}

								}
								else {
									if (x[4] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}
							else {
								if (x[10] <= 1.5) {
									if (x[11] <= 0.5) {
										if (x[6] <= 21.5) {
											if (x[7] <= 0.5) {
												if (x[2] <= 0.5) {
													return 14.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 1.5) {
														return 1.0f;
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
											if (x[6] <= 22.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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

									}
									else {
										if (x[6] <= 21.5) {
											if (x[7] <= 0.5) {
												if (x[2] <= 0.5) {
													return 14.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 1.5) {
														return 1.0f;
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
											if (x[6] <= 22.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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

									}

								}
								else {
									if (x[6] <= 21.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[6] <= 22.5) {
											if (x[7] <= 0.5) {
												if (x[11] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[11] <= 1.5) {
														return 15.0f;
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
														return 3.0f;
													}

												}
												else {
													return 2.0f;
												}

											}

										}
										else {
											if (x[11] <= 1.0) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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

									}

								}

							}

						}

					}
					else {
						if (x[9] <= 0.5) {
							if (x[10] <= 0.5) {
								if (x[6] <= 21.5) {
									if (x[7] <= 0.5) {
										if (x[4] <= 0.5) {
											if (x[11] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[11] <= 1.5) {
													return 15.0f;
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
										if (x[0] <= 0.5) {
											if (x[7] <= 1.5) {
												return 1.0f;
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
									if (x[6] <= 22.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}
							else {
								if (x[10] <= 1.5) {
									if (x[11] <= 0.5) {
										if (x[6] <= 21.5) {
											if (x[7] <= 0.5) {
												if (x[3] <= 0.5) {
													return 14.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 1.5) {
														return 1.0f;
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
											if (x[6] <= 22.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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

									}
									else {
										if (x[6] <= 21.5) {
											if (x[7] <= 0.5) {
												if (x[3] <= 0.5) {
													return 14.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 1.5) {
														return 1.0f;
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
											if (x[6] <= 22.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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

									}

								}
								else {
									if (x[6] <= 21.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[6] <= 22.5) {
											if (x[7] <= 0.5) {
												if (x[11] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[11] <= 1.5) {
														return 15.0f;
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
														return 3.0f;
													}

												}
												else {
													return 2.0f;
												}

											}

										}
										else {
											if (x[11] <= 1.0) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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

									}

								}

							}

						}
						else {
							if (x[10] <= 0.5) {
								if (x[9] <= 1.5) {
									if (x[11] <= 0.5) {
										if (x[6] <= 21.5) {
											if (x[7] <= 0.5) {
												if (x[2] <= 0.5) {
													return 13.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 1.5) {
														return 1.0f;
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
											if (x[6] <= 22.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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

									}
									else {
										if (x[6] <= 21.5) {
											if (x[7] <= 0.5) {
												if (x[2] <= 0.5) {
													return 13.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 1.5) {
														return 1.0f;
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
											if (x[6] <= 22.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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

									}

								}
								else {
									if (x[6] <= 21.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[6] <= 22.5) {
											if (x[7] <= 0.5) {
												if (x[11] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[11] <= 1.5) {
														return 15.0f;
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
														return 3.0f;
													}

												}
												else {
													return 2.0f;
												}

											}

										}
										else {
											if (x[11] <= 1.0) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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

									}

								}

							}
							else {
								if (x[10] <= 1.5) {
									if (x[6] <= 21.5) {
										if (x[11] <= 0.5) {
											if (x[2] <= 0.5) {
												if (x[7] <= 0.5) {
													if (x[9] <= 1.5) {
														return 13.0f;
													}
													else {
														return 0.0f;
													}

												}
												else {
													if (x[0] <= 0.5) {
														if (x[7] <= 1.5) {
															return 1.0f;
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
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[2] <= 0.5) {
												if (x[7] <= 0.5) {
													if (x[9] <= 1.5) {
														return 13.0f;
													}
													else {
														return 0.0f;
													}

												}
												else {
													if (x[0] <= 0.5) {
														if (x[7] <= 1.5) {
															return 1.0f;
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
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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

									}
									else {
										if (x[11] <= 0.5) {
											if (x[6] <= 22.5) {
												if (x[7] <= 0.5) {
													if (x[2] <= 0.5) {
														return 14.0f;
													}
													else {
														return 0.0f;
													}

												}
												else {
													if (x[0] <= 0.5) {
														if (x[7] <= 1.5) {
															return 1.0f;
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
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[6] <= 22.5) {
												if (x[7] <= 0.5) {
													if (x[2] <= 0.5) {
														return 14.0f;
													}
													else {
														return 0.0f;
													}

												}
												else {
													if (x[0] <= 0.5) {
														if (x[7] <= 1.5) {
															return 1.0f;
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
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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

									}

								}
								else {
									if (x[7] <= 0.5) {
										if (x[6] <= 21.5) {
											if (x[11] <= 1.5) {
												return 0.0f;
											}
											else {
												return 4.0f;
											}

										}
										else {
											if (x[6] <= 22.5) {
												return 0.0f;
											}
											else {
												if (x[11] <= 0.5) {
													return 0.0f;
												}
												else {
													if (x[11] <= 1.5) {
														return 15.0f;
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
											if (x[7] <= 1.5) {
												return 1.0f;
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
					if (x[2] <= 0.5) {
						if (x[9] <= 1.0) {
							if (x[10] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[3] <= 0.5) {
									if (x[11] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[4] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}

						}
						else {
							if (x[10] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[3] <= 0.5) {
									if (x[11] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[4] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}

						}

					}
					else {
						if (x[3] <= 0.5) {
							if (x[10] <= 1.0) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							if (x[4] <= 0.5) {
								if (x[11] <= 1.0) {
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
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
								else {
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
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
								if (x[12] <= 1.0) {
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
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
								else {
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
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

						}

					}

				}

			}

		}
		else {
			if (x[6] <= 26.5) {
				if (x[1] <= 0.5) {
					if (x[8] <= 1.0) {
						if (x[9] <= 0.5) {
							if (x[10] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[3] <= 0.5) {
									if (x[11] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[4] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}

						}
						else {
							if (x[2] <= 0.5) {
								if (x[10] <= 1.0) {
									if (x[11] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[11] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}
							else {
								if (x[3] <= 0.5) {
									if (x[4] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[4] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}

						}

					}
					else {
						if (x[9] <= 0.5) {
							if (x[10] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[3] <= 0.5) {
									if (x[11] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[4] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}

						}
						else {
							if (x[2] <= 0.5) {
								if (x[10] <= 1.0) {
									if (x[11] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[11] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}
							else {
								if (x[3] <= 0.5) {
									if (x[4] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[4] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}

						}

					}

				}
				else {
					if (x[2] <= 0.5) {
						if (x[9] <= 1.0) {
							if (x[10] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[3] <= 0.5) {
									if (x[11] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[4] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}

						}
						else {
							if (x[10] <= 0.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[3] <= 0.5) {
									if (x[11] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[4] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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

							}

						}

					}
					else {
						if (x[3] <= 0.5) {
							if (x[10] <= 1.0) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							else {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[7] <= 1.5) {
											return 1.0f;
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
							if (x[4] <= 0.5) {
								if (x[11] <= 1.0) {
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
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
								else {
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
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
								if (x[12] <= 1.0) {
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
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
								else {
									if (x[0] <= 0.5) {
										if (x[7] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[7] <= 1.5) {
												return 1.0f;
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

						}

					}

				}

			}
			else {
				if (x[1] <= 0.5) {
					if (x[8] <= 0.5) {
						if (x[9] <= 0.5) {
							if (x[10] <= 0.5) {
								if (x[6] <= 28.5) {
									if (x[6] <= 27.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[7] <= 1.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[11] <= 1.5) {
												return 2.0f;
											}
											else {
												return 17.0f;
											}

										}

									}
									else {
										if (x[6] <= 29.5) {
											return 3.0f;
										}
										else {
											return 17.0f;
										}

									}

								}

							}
							else {
								if (x[11] <= 0.5) {
									if (x[3] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												return 17.0f;
											}

										}

									}
									else {
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
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
												if (x[6] <= 29.5) {
													return 3.0f;
												}
												else {
													return 17.0f;
												}

											}

										}

									}

								}
								else {
									if (x[3] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												return 17.0f;
											}

										}

									}
									else {
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
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
												if (x[6] <= 29.5) {
													return 3.0f;
												}
												else {
													return 17.0f;
												}

											}

										}

									}

								}

							}

						}
						else {
							if (x[10] <= 0.5) {
								if (x[11] <= 0.5) {
									if (x[2] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												return 17.0f;
											}

										}

									}
									else {
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
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
												if (x[6] <= 29.5) {
													return 3.0f;
												}
												else {
													return 17.0f;
												}

											}

										}

									}

								}
								else {
									if (x[2] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												return 17.0f;
											}

										}

									}
									else {
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
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
												if (x[6] <= 29.5) {
													return 3.0f;
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
								if (x[11] <= 0.5) {
									if (x[2] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												return 17.0f;
											}

										}

									}
									else {
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
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
												if (x[6] <= 29.5) {
													return 3.0f;
												}
												else {
													return 17.0f;
												}

											}

										}

									}

								}
								else {
									if (x[2] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												return 17.0f;
											}

										}

									}
									else {
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
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
												if (x[6] <= 29.5) {
													return 3.0f;
												}
												else {
													return 17.0f;
												}

											}

										}

									}

								}

							}

						}

					}
					else {
						if (x[9] <= 0.5) {
							if (x[10] <= 0.5) {
								if (x[6] <= 28.5) {
									if (x[6] <= 27.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[7] <= 1.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[8] <= 1.5) {
												return 12.0f;
											}
											else {
												return 4.0f;
											}

										}

									}
									else {
										if (x[6] <= 29.5) {
											return 3.0f;
										}
										else {
											return 12.0f;
										}

									}

								}

							}
							else {
								if (x[3] <= 0.5) {
									if (x[11] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 12.0f;
												}
												else {
													return 4.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 12.0f;
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
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														return 1.0f;
													}

												}
												else {
													return 4.0f;
												}

											}
											else {
												if (x[6] <= 29.5) {
													return 3.0f;
												}
												else {
													return 12.0f;
												}

											}

										}

									}
									else {
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														return 1.0f;
													}

												}
												else {
													return 4.0f;
												}

											}
											else {
												if (x[6] <= 29.5) {
													return 3.0f;
												}
												else {
													return 12.0f;
												}

											}

										}

									}

								}

							}

						}
						else {
							if (x[2] <= 0.5) {
								if (x[10] <= 1.0) {
									if (x[11] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 12.0f;
												}
												else {
													return 4.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 12.0f;
												}
												else {
													return 4.0f;
												}

											}

										}

									}

								}
								else {
									if (x[11] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 12.0f;
												}
												else {
													return 4.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												if (x[8] <= 1.5) {
													return 12.0f;
												}
												else {
													return 4.0f;
												}

											}

										}

									}

								}

							}
							else {
								if (x[3] <= 0.5) {
									if (x[4] <= 0.5) {
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														return 1.0f;
													}

												}
												else {
													return 4.0f;
												}

											}
											else {
												if (x[6] <= 29.5) {
													return 3.0f;
												}
												else {
													return 12.0f;
												}

											}

										}

									}
									else {
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														return 1.0f;
													}

												}
												else {
													return 4.0f;
												}

											}
											else {
												if (x[6] <= 29.5) {
													return 3.0f;
												}
												else {
													return 12.0f;
												}

											}

										}

									}

								}
								else {
									if (x[4] <= 0.5) {
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														return 1.0f;
													}

												}
												else {
													return 4.0f;
												}

											}
											else {
												if (x[6] <= 29.5) {
													return 3.0f;
												}
												else {
													return 12.0f;
												}

											}

										}

									}
									else {
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														return 1.0f;
													}

												}
												else {
													return 4.0f;
												}

											}
											else {
												if (x[0] <= 0.5) {
													if (x[6] <= 29.5) {
														return 3.0f;
													}
													else {
														return 12.0f;
													}

												}
												else {
													return 27.0f;
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
					if (x[2] <= 0.5) {
						if (x[9] <= 0.5) {
							if (x[10] <= 0.5) {
								if (x[6] <= 28.5) {
									if (x[6] <= 27.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[7] <= 1.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[11] <= 1.5) {
												return 2.0f;
											}
											else {
												return 18.0f;
											}

										}

									}
									else {
										if (x[6] <= 29.5) {
											return 3.0f;
										}
										else {
											return 18.0f;
										}

									}

								}

							}
							else {
								if (x[11] <= 0.5) {
									if (x[3] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												return 18.0f;
											}

										}

									}
									else {
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
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
												if (x[6] <= 29.5) {
													return 3.0f;
												}
												else {
													return 18.0f;
												}

											}

										}

									}

								}
								else {
									if (x[3] <= 0.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												return 18.0f;
											}

										}

									}
									else {
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
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
												if (x[6] <= 29.5) {
													return 3.0f;
												}
												else {
													return 18.0f;
												}

											}

										}

									}

								}

							}

						}
						else {
							if (x[10] <= 0.5) {
								if (x[6] <= 28.5) {
									if (x[6] <= 27.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[7] <= 1.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[9] <= 1.5) {
												return 13.0f;
											}
											else {
												return 5.0f;
											}

										}

									}
									else {
										if (x[6] <= 29.5) {
											return 3.0f;
										}
										else {
											return 13.0f;
										}

									}

								}

							}
							else {
								if (x[3] <= 0.5) {
									if (x[11] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												if (x[9] <= 1.5) {
													return 13.0f;
												}
												else {
													return 5.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												if (x[9] <= 1.5) {
													return 13.0f;
												}
												else {
													return 5.0f;
												}

											}

										}

									}

								}
								else {
									if (x[4] <= 0.5) {
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
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
												if (x[6] <= 29.5) {
													return 3.0f;
												}
												else {
													return 13.0f;
												}

											}

										}

									}
									else {
										if (x[6] <= 28.5) {
											if (x[6] <= 27.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											else {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
													}
													else {
														if (x[7] <= 1.5) {
															return 1.0f;
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
											if (x[7] <= 1.5) {
												if (x[0] <= 0.5) {
													if (x[7] <= 0.5) {
														return 0.0f;
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
												if (x[0] <= 0.5) {
													if (x[6] <= 29.5) {
														return 3.0f;
													}
													else {
														return 13.0f;
													}

												}
												else {
													return 29.0f;
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
							if (x[10] <= 0.5) {
								if (x[6] <= 28.5) {
									if (x[6] <= 27.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[7] <= 1.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[11] <= 1.5) {
												return 2.0f;
											}
											else {
												return 19.0f;
											}

										}

									}
									else {
										if (x[6] <= 29.5) {
											return 3.0f;
										}
										else {
											return 19.0f;
										}

									}

								}

							}
							else {
								if (x[6] <= 28.5) {
									if (x[6] <= 27.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												if (x[7] <= 1.5) {
													return 1.0f;
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
									if (x[7] <= 1.5) {
										if (x[0] <= 0.5) {
											if (x[7] <= 0.5) {
												return 0.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[10] <= 1.5) {
												return 14.0f;
											}
											else {
												return 6.0f;
											}

										}

									}
									else {
										if (x[6] <= 29.5) {
											return 3.0f;
										}
										else {
											if (x[0] <= 0.5) {
												return 14.0f;
											}
											else {
												return 31.0f;
											}

										}

									}

								}

							}

						}
						else {
							if (x[7] <= 1.5) {
								if (x[0] <= 0.5) {
									if (x[7] <= 0.5) {
										return 0.0f;
									}
									else {
										return 1.0f;
									}

								}
								else {
									if (x[4] <= 0.5) {
										if (x[6] <= 27.5) {
											return 2.0f;
										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												if (x[11] <= 1.0) {
													return 2.0f;
												}
												else {
													return 7.0f;
												}

											}

										}

									}
									else {
										if (x[6] <= 27.5) {
											return 2.0f;
										}
										else {
											if (x[6] <= 28.5) {
												return 2.0f;
											}
											else {
												if (x[12] <= 1.0) {
													return 2.0f;
												}
												else {
													return 16.0f;
												}

											}

										}

									}

								}

							}
							else {
								if (x[6] <= 30.5) {
									if (x[12] <= 0.5) {
										if (x[4] <= 0.5) {
											if (x[6] <= 29.5) {
												return 3.0f;
											}
											else {
												if (x[11] <= 0.5) {
													return 20.0f;
												}
												else {
													return 15.0f;
												}

											}

										}
										else {
											if (x[6] <= 29.5) {
												return 3.0f;
											}
											else {
												return 21.0f;
											}

										}

									}
									else {
										if (x[5] <= 0.5) {
											if (x[6] <= 29.5) {
												return 3.0f;
											}
											else {
												return 24.0f;
											}

										}
										else {
											if (x[0] <= 0.5) {
												return 25.0f;
											}
											else {
												return 8.0f;
											}

										}

									}

								}
								else {
									if (x[6] <= 33.5) {
										if (x[6] <= 31.5) {
											return 9.0f;
										}
										else {
											if (x[6] <= 32.5) {
												return 10.0f;
											}
											else {
												return 11.0f;
											}

										}

									}
									else {
										if (x[6] <= 34.5) {
											if (x[4] <= 0.5) {
												return 33.0f;
											}
											else {
												return 23.0f;
											}

										}
										else {
											if (x[5] <= 0.5) {
												return 35.0f;
											}
											else {
												return 36.0f;
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