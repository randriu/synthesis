#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[0] <= 3.5) {
		if (x[1] <= 3.5) {
			if (x[3] <= 1.5) {
				if (x[2] <= 3.5) {
					if (x[3] <= 0.5) {
						if (x[2] <= 1.5) {
							if (x[2] <= 0.5) {
								return 0.0f;
							}
							else {
								if (x[1] <= 0.5) {
									return 0.0f;
								}
								else {
									if (x[0] <= 1.5) {
										if (x[1] <= 2.5) {
											return 2.0f;
										}
										else {
											if (x[0] <= 0.5) {
												return 2.0f;
											}
											else {
												return 7.0f;
											}

										}

									}
									else {
										if (x[1] <= 1.5) {
											return 2.0f;
										}
										else {
											if (x[0] <= 2.5) {
												if (x[1] <= 2.5) {
													return 2.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[1] <= 2.5) {
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
							if (x[1] <= 1.5) {
								if (x[1] <= 0.5) {
									if (x[0] <= 1.5) {
										if (x[0] <= 0.5) {
											return 0.0f;
										}
										else {
											if (x[2] <= 2.5) {
												return 7.0f;
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
										if (x[0] <= 0.5) {
											return 11.0f;
										}
										else {
											if (x[2] <= 2.5) {
												return 11.0f;
											}
											else {
												return 7.0f;
											}

										}

									}
									else {
										if (x[0] <= 2.5) {
											if (x[2] <= 2.5) {
												return 11.0f;
											}
											else {
												return 0.0f;
											}

										}
										else {
											if (x[2] <= 2.5) {
												return 0.0f;
											}
											else {
												return 11.0f;
											}

										}

									}

								}

							}
							else {
								if (x[1] <= 2.5) {
									if (x[2] <= 2.5) {
										if (x[0] <= 2.5) {
											return 9.0f;
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
									if (x[2] <= 2.5) {
										return 0.0f;
									}
									else {
										if (x[0] <= 1.5) {
											if (x[0] <= 0.5) {
												return 16.0f;
											}
											else {
												return 7.0f;
											}

										}
										else {
											if (x[0] <= 2.5) {
												return 0.0f;
											}
											else {
												return 19.0f;
											}

										}

									}

								}

							}

						}

					}
					else {
						if (x[1] <= 1.5) {
							if (x[1] <= 0.5) {
								if (x[0] <= 1.5) {
									if (x[0] <= 0.5) {
										return 1.0f;
									}
									else {
										if (x[2] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[2] <= 2.5) {
												return 7.0f;
											}
											else {
												return 1.0f;
											}

										}

									}

								}
								else {
									return 1.0f;
								}

							}
							else {
								if (x[2] <= 1.5) {
									if (x[0] <= 2.5) {
										if (x[2] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[0] <= 0.5) {
												return 1.0f;
											}
											else {
												if (x[0] <= 1.5) {
													return 7.0f;
												}
												else {
													return 1.0f;
												}

											}

										}

									}
									else {
										if (x[2] <= 0.5) {
											return 1.0f;
										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[0] <= 1.5) {
										if (x[0] <= 0.5) {
											if (x[2] <= 2.5) {
												return 1.0f;
											}
											else {
												return 11.0f;
											}

										}
										else {
											if (x[2] <= 2.5) {
												return 11.0f;
											}
											else {
												return 7.0f;
											}

										}

									}
									else {
										if (x[0] <= 2.5) {
											if (x[2] <= 2.5) {
												return 11.0f;
											}
											else {
												return 1.0f;
											}

										}
										else {
											if (x[2] <= 2.5) {
												return 1.0f;
											}
											else {
												return 11.0f;
											}

										}

									}

								}

							}

						}
						else {
							if (x[1] <= 2.5) {
								if (x[0] <= 2.5) {
									if (x[0] <= 0.5) {
										if (x[2] <= 0.5) {
											return 9.0f;
										}
										else {
											return 1.0f;
										}

									}
									else {
										if (x[2] <= 2.5) {
											return 9.0f;
										}
										else {
											if (x[0] <= 1.5) {
												return 1.0f;
											}
											else {
												return 9.0f;
											}

										}

									}

								}
								else {
									return 1.0f;
								}

							}
							else {
								if (x[2] <= 2.5) {
									if (x[2] <= 0.5) {
										if (x[0] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[0] <= 2.5) {
												return 3.0f;
											}
											else {
												return 1.0f;
											}

										}

									}
									else {
										if (x[2] <= 1.5) {
											if (x[0] <= 1.5) {
												if (x[0] <= 0.5) {
													return 2.0f;
												}
												else {
													return 7.0f;
												}

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
									if (x[0] <= 1.5) {
										if (x[0] <= 0.5) {
											return 19.0f;
										}
										else {
											return 7.0f;
										}

									}
									else {
										if (x[0] <= 2.5) {
											return 16.0f;
										}
										else {
											return 19.0f;
										}

									}

								}

							}

						}

					}

				}
				else {
					if (x[2] <= 4.5) {
						if (x[3] <= 0.5) {
							if (x[1] <= 1.5) {
								if (x[1] <= 0.5) {
									return 12.0f;
								}
								else {
									if (x[0] <= 2.5) {
										return 11.0f;
									}
									else {
										return 12.0f;
									}

								}

							}
							else {
								if (x[1] <= 2.5) {
									if (x[0] <= 2.5) {
										return 9.0f;
									}
									else {
										return 12.0f;
									}

								}
								else {
									return 12.0f;
								}

							}

						}
						else {
							if (x[0] <= 2.5) {
								return 12.0f;
							}
							else {
								if (x[1] <= 2.5) {
									return 12.0f;
								}
								else {
									return 19.0f;
								}

							}

						}

					}
					else {
						if (x[1] <= 2.5) {
							if (x[2] <= 5.5) {
								if (x[1] <= 0.5) {
									return 13.0f;
								}
								else {
									if (x[1] <= 1.5) {
										if (x[0] <= 1.5) {
											if (x[0] <= 0.5) {
												if (x[3] <= 0.5) {
													return 11.0f;
												}
												else {
													return 13.0f;
												}

											}
											else {
												return 7.0f;
											}

										}
										else {
											if (x[0] <= 2.5) {
												if (x[3] <= 0.5) {
													return 11.0f;
												}
												else {
													return 13.0f;
												}

											}
											else {
												return 11.0f;
											}

										}

									}
									else {
										return 13.0f;
									}

								}

							}
							else {
								if (x[1] <= 1.5) {
									if (x[2] <= 6.5) {
										if (x[0] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[0] <= 2.5) {
												return 11.0f;
											}
											else {
												return 15.0f;
											}

										}

									}
									else {
										return 11.0f;
									}

								}
								else {
									if (x[0] <= 1.5) {
										if (x[2] <= 6.5) {
											return 7.0f;
										}
										else {
											return 28.0f;
										}

									}
									else {
										if (x[0] <= 2.5) {
											if (x[2] <= 6.5) {
												return 1.0f;
											}
											else {
												return 28.0f;
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
							if (x[0] <= 2.5) {
								if (x[2] <= 5.5) {
									if (x[0] <= 1.5) {
										return 19.0f;
									}
									else {
										if (x[3] <= 0.5) {
											return 13.0f;
										}
										else {
											return 19.0f;
										}

									}

								}
								else {
									if (x[0] <= 1.5) {
										if (x[2] <= 6.5) {
											return 1.0f;
										}
										else {
											return 19.0f;
										}

									}
									else {
										return 1.0f;
									}

								}

							}
							else {
								if (x[2] <= 6.5) {
									if (x[2] <= 5.5) {
										if (x[3] <= 0.5) {
											return 15.0f;
										}
										else {
											return 19.0f;
										}

									}
									else {
										return 15.0f;
									}

								}
								else {
									return 19.0f;
								}

							}

						}

					}

				}

			}
			else {
				if (x[0] <= 1.5) {
					if (x[0] <= 0.5) {
						if (x[2] <= 2.5) {
							if (x[2] <= 1.5) {
								if (x[2] <= 0.5) {
									if (x[3] <= 4.5) {
										if (x[1] <= 0.5) {
											if (x[3] <= 2.5) {
												return 3.0f;
											}
											else {
												if (x[3] <= 3.5) {
													return 4.0f;
												}
												else {
													return 3.0f;
												}

											}

										}
										else {
											if (x[1] <= 2.5) {
												return 4.0f;
											}
											else {
												if (x[3] <= 2.5) {
													return 3.0f;
												}
												else {
													if (x[3] <= 3.5) {
														return 4.0f;
													}
													else {
														return 3.0f;
													}

												}

											}

										}

									}
									else {
										return 4.0f;
									}

								}
								else {
									if (x[3] <= 4.5) {
										return 2.0f;
									}
									else {
										if (x[1] <= 1.5) {
											if (x[1] <= 0.5) {
												return 2.0f;
											}
											else {
												return 11.0f;
											}

										}
										else {
											if (x[1] <= 2.5) {
												return 4.0f;
											}
											else {
												return 19.0f;
											}

										}

									}

								}

							}
							else {
								if (x[3] <= 4.5) {
									if (x[3] <= 2.5) {
										return 17.0f;
									}
									else {
										if (x[3] <= 3.5) {
											if (x[1] <= 1.5) {
												return 4.0f;
											}
											else {
												if (x[1] <= 2.5) {
													return 9.0f;
												}
												else {
													return 4.0f;
												}

											}

										}
										else {
											return 17.0f;
										}

									}

								}
								else {
									return 4.0f;
								}

							}

						}
						else {
							if (x[1] <= 1.5) {
								if (x[1] <= 0.5) {
									if (x[3] <= 3.5) {
										if (x[3] <= 2.5) {
											if (x[2] <= 3.5) {
												return 18.0f;
											}
											else {
												if (x[2] <= 4.5) {
													return 12.0f;
												}
												else {
													return 18.0f;
												}

											}

										}
										else {
											if (x[2] <= 3.5) {
												return 16.0f;
											}
											else {
												if (x[2] <= 4.5) {
													return 18.0f;
												}
												else {
													return 13.0f;
												}

											}

										}

									}
									else {
										if (x[2] <= 3.5) {
											if (x[3] <= 4.5) {
												return 4.0f;
											}
											else {
												return 16.0f;
											}

										}
										else {
											if (x[3] <= 4.5) {
												if (x[2] <= 4.5) {
													return 4.0f;
												}
												else {
													return 18.0f;
												}

											}
											else {
												return 4.0f;
											}

										}

									}

								}
								else {
									if (x[2] <= 6.0) {
										if (x[3] <= 2.5) {
											if (x[2] <= 3.5) {
												return 11.0f;
											}
											else {
												if (x[2] <= 4.5) {
													return 12.0f;
												}
												else {
													return 11.0f;
												}

											}

										}
										else {
											if (x[2] <= 3.5) {
												if (x[3] <= 3.5) {
													return 11.0f;
												}
												else {
													if (x[3] <= 4.5) {
														return 4.0f;
													}
													else {
														return 11.0f;
													}

												}

											}
											else {
												return 11.0f;
											}

										}

									}
									else {
										return 4.0f;
									}

								}

							}
							else {
								if (x[1] <= 2.5) {
									if (x[2] <= 4.5) {
										if (x[2] <= 3.5) {
											if (x[3] <= 2.5) {
												return 4.0f;
											}
											else {
												if (x[3] <= 3.5) {
													return 16.0f;
												}
												else {
													if (x[3] <= 4.5) {
														return 4.0f;
													}
													else {
														return 16.0f;
													}

												}

											}

										}
										else {
											if (x[3] <= 2.5) {
												return 12.0f;
											}
											else {
												return 9.0f;
											}

										}

									}
									else {
										if (x[3] <= 3.5) {
											if (x[3] <= 2.5) {
												return 4.0f;
											}
											else {
												return 13.0f;
											}

										}
										else {
											return 4.0f;
										}

									}

								}
								else {
									if (x[3] <= 4.5) {
										if (x[3] <= 2.5) {
											if (x[2] <= 3.5) {
												return 19.0f;
											}
											else {
												if (x[2] <= 4.5) {
													return 12.0f;
												}
												else {
													return 19.0f;
												}

											}

										}
										else {
											if (x[2] <= 3.5) {
												return 19.0f;
											}
											else {
												if (x[2] <= 4.5) {
													return 4.0f;
												}
												else {
													return 19.0f;
												}

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
						if (x[1] <= 1.5) {
							if (x[1] <= 0.5) {
								if (x[2] <= 2.5) {
									if (x[2] <= 1.5) {
										if (x[2] <= 0.5) {
											return 7.0f;
										}
										else {
											if (x[3] <= 2.5) {
												return 7.0f;
											}
											else {
												return 2.0f;
											}

										}

									}
									else {
										if (x[3] <= 2.5) {
											return 17.0f;
										}
										else {
											if (x[3] <= 3.5) {
												return 7.0f;
											}
											else {
												if (x[3] <= 4.5) {
													return 17.0f;
												}
												else {
													return 7.0f;
												}

											}

										}

									}

								}
								else {
									if (x[3] <= 3.5) {
										if (x[3] <= 2.5) {
											if (x[2] <= 3.5) {
												return 18.0f;
											}
											else {
												if (x[2] <= 4.5) {
													return 12.0f;
												}
												else {
													return 18.0f;
												}

											}

										}
										else {
											if (x[2] <= 3.5) {
												return 16.0f;
											}
											else {
												if (x[2] <= 4.5) {
													return 18.0f;
												}
												else {
													return 13.0f;
												}

											}

										}

									}
									else {
										if (x[2] <= 3.5) {
											if (x[3] <= 4.5) {
												return 7.0f;
											}
											else {
												return 16.0f;
											}

										}
										else {
											return 7.0f;
										}

									}

								}

							}
							else {
								if (x[2] <= 2.5) {
									if (x[3] <= 3.5) {
										if (x[2] <= 1.5) {
											return 7.0f;
										}
										else {
											if (x[3] <= 2.5) {
												return 17.0f;
											}
											else {
												return 7.0f;
											}

										}

									}
									else {
										if (x[3] <= 4.5) {
											if (x[2] <= 0.5) {
												return 7.0f;
											}
											else {
												if (x[2] <= 1.5) {
													return 2.0f;
												}
												else {
													return 11.0f;
												}

											}

										}
										else {
											if (x[2] <= 0.5) {
												return 7.0f;
											}
											else {
												if (x[3] <= 5.5) {
													if (x[2] <= 1.5) {
														return 11.0f;
													}
													else {
														return 7.0f;
													}

												}
												else {
													if (x[2] <= 1.5) {
														return 7.0f;
													}
													else {
														if (x[3] <= 6.5) {
															return 7.0f;
														}
														else {
															return 11.0f;
														}

													}

												}

											}

										}

									}

								}
								else {
									if (x[3] <= 2.5) {
										if (x[2] <= 5.5) {
											return 11.0f;
										}
										else {
											if (x[2] <= 6.5) {
												return 38.0f;
											}
											else {
												return 11.0f;
											}

										}

									}
									else {
										if (x[3] <= 6.5) {
											if (x[2] <= 5.5) {
												if (x[2] <= 4.5) {
													if (x[3] <= 3.5) {
														return 11.0f;
													}
													else {
														if (x[2] <= 3.5) {
															if (x[3] <= 4.5) {
																return 7.0f;
															}
															else {
																if (x[3] <= 5.5) {
																	return 11.0f;
																}
																else {
																	return 7.0f;
																}

															}

														}
														else {
															return 7.0f;
														}

													}

												}
												else {
													return 11.0f;
												}

											}
											else {
												if (x[3] <= 3.5) {
													return 7.0f;
												}
												else {
													if (x[2] <= 6.5) {
														if (x[3] <= 5.0) {
															return 34.0f;
														}
														else {
															return 11.0f;
														}

													}
													else {
														if (x[3] <= 4.5) {
															return 11.0f;
														}
														else {
															return 7.0f;
														}

													}

												}

											}

										}
										else {
											return 7.0f;
										}

									}

								}

							}

						}
						else {
							if (x[1] <= 2.5) {
								if (x[3] <= 6.5) {
									if (x[2] <= 4.5) {
										if (x[2] <= 1.5) {
											return 7.0f;
										}
										else {
											if (x[2] <= 2.5) {
												if (x[3] <= 3.5) {
													return 9.0f;
												}
												else {
													if (x[3] <= 5.5) {
														return 7.0f;
													}
													else {
														return 9.0f;
													}

												}

											}
											else {
												if (x[2] <= 3.5) {
													if (x[3] <= 2.5) {
														return 7.0f;
													}
													else {
														if (x[3] <= 3.5) {
															return 16.0f;
														}
														else {
															if (x[3] <= 4.5) {
																return 7.0f;
															}
															else {
																if (x[3] <= 5.5) {
																	return 16.0f;
																}
																else {
																	return 7.0f;
																}

															}

														}

													}

												}
												else {
													if (x[3] <= 2.5) {
														return 7.0f;
													}
													else {
														if (x[3] <= 3.5) {
															return 9.0f;
														}
														else {
															if (x[3] <= 5.0) {
																return 7.0f;
															}
															else {
																return 9.0f;
															}

														}

													}

												}

											}

										}

									}
									else {
										if (x[3] <= 3.5) {
											if (x[3] <= 2.5) {
												if (x[2] <= 6.5) {
													return 7.0f;
												}
												else {
													return 28.0f;
												}

											}
											else {
												if (x[2] <= 5.5) {
													return 13.0f;
												}
												else {
													if (x[2] <= 6.5) {
														return 32.0f;
													}
													else {
														return 7.0f;
													}

												}

											}

										}
										else {
											return 7.0f;
										}

									}

								}
								else {
									if (x[2] <= 1.5) {
										return 7.0f;
									}
									else {
										if (x[2] <= 4.0) {
											if (x[2] <= 2.5) {
												return 37.0f;
											}
											else {
												return 16.0f;
											}

										}
										else {
											if (x[2] <= 6.0) {
												return 27.0f;
											}
											else {
												return 37.0f;
											}

										}

									}

								}

							}
							else {
								if (x[3] <= 2.5) {
									if (x[2] <= 2.5) {
										if (x[2] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[2] <= 1.5) {
												return 2.0f;
											}
											else {
												return 17.0f;
											}

										}

									}
									else {
										if (x[2] <= 4.5) {
											if (x[2] <= 3.5) {
												return 19.0f;
											}
											else {
												return 12.0f;
											}

										}
										else {
											if (x[2] <= 5.5) {
												return 19.0f;
											}
											else {
												if (x[2] <= 6.5) {
													return 38.0f;
												}
												else {
													return 19.0f;
												}

											}

										}

									}

								}
								else {
									if (x[2] <= 2.5) {
										if (x[3] <= 4.5) {
											if (x[3] <= 3.5) {
												return 7.0f;
											}
											else {
												if (x[2] <= 0.5) {
													return 7.0f;
												}
												else {
													if (x[2] <= 1.5) {
														return 2.0f;
													}
													else {
														return 17.0f;
													}

												}

											}

										}
										else {
											if (x[3] <= 5.5) {
												if (x[2] <= 0.5) {
													return 7.0f;
												}
												else {
													if (x[2] <= 1.5) {
														return 19.0f;
													}
													else {
														return 7.0f;
													}

												}

											}
											else {
												return 7.0f;
											}

										}

									}
									else {
										if (x[3] <= 4.5) {
											if (x[2] <= 3.5) {
												return 19.0f;
											}
											else {
												if (x[2] <= 4.5) {
													return 7.0f;
												}
												else {
													if (x[2] <= 5.5) {
														return 19.0f;
													}
													else {
														if (x[2] <= 6.5) {
															return 7.0f;
														}
														else {
															if (x[3] <= 3.5) {
																return 7.0f;
															}
															else {
																return 19.0f;
															}

														}

													}

												}

											}

										}
										else {
											if (x[2] <= 4.5) {
												return 7.0f;
											}
											else {
												if (x[2] <= 5.5) {
													if (x[3] <= 5.5) {
														return 7.0f;
													}
													else {
														if (x[3] <= 6.5) {
															return 19.0f;
														}
														else {
															return 7.0f;
														}

													}

												}
												else {
													return 7.0f;
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
					if (x[0] <= 2.5) {
						if (x[2] <= 1.5) {
							if (x[2] <= 0.5) {
								if (x[3] <= 2.5) {
									return 14.0f;
								}
								else {
									if (x[3] <= 3.5) {
										return 3.0f;
									}
									else {
										if (x[3] <= 4.5) {
											return 14.0f;
										}
										else {
											return 3.0f;
										}

									}

								}

							}
							else {
								if (x[3] <= 2.5) {
									return 14.0f;
								}
								else {
									if (x[3] <= 3.5) {
										return 2.0f;
									}
									else {
										if (x[3] <= 4.5) {
											return 14.0f;
										}
										else {
											if (x[3] <= 5.5) {
												if (x[1] <= 1.5) {
													return 2.0f;
												}
												else {
													if (x[1] <= 2.5) {
														return 9.0f;
													}
													else {
														return 2.0f;
													}

												}

											}
											else {
												if (x[1] <= 2.5) {
													return 14.0f;
												}
												else {
													if (x[3] <= 6.5) {
														return 14.0f;
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
							if (x[1] <= 2.5) {
								if (x[1] <= 1.5) {
									if (x[1] <= 0.5) {
										if (x[3] <= 2.5) {
											if (x[2] <= 3.5) {
												return 14.0f;
											}
											else {
												if (x[2] <= 4.5) {
													return 12.0f;
												}
												else {
													return 14.0f;
												}

											}

										}
										else {
											if (x[3] <= 3.5) {
												if (x[2] <= 4.5) {
													if (x[2] <= 2.5) {
														return 18.0f;
													}
													else {
														if (x[2] <= 3.5) {
															return 16.0f;
														}
														else {
															return 18.0f;
														}

													}

												}
												else {
													return 13.0f;
												}

											}
											else {
												if (x[3] <= 4.5) {
													return 14.0f;
												}
												else {
													if (x[3] <= 5.5) {
														if (x[2] <= 4.0) {
															if (x[2] <= 2.5) {
																return 18.0f;
															}
															else {
																return 16.0f;
															}

														}
														else {
															return 18.0f;
														}

													}
													else {
														return 14.0f;
													}

												}

											}

										}

									}
									else {
										if (x[2] <= 3.5) {
											if (x[2] <= 2.5) {
												if (x[3] <= 6.5) {
													if (x[3] <= 2.5) {
														return 14.0f;
													}
													else {
														if (x[3] <= 3.5) {
															return 11.0f;
														}
														else {
															if (x[3] <= 4.5) {
																return 14.0f;
															}
															else {
																if (x[3] <= 5.5) {
																	return 11.0f;
																}
																else {
																	return 14.0f;
																}

															}

														}

													}

												}
												else {
													return 37.0f;
												}

											}
											else {
												if (x[3] <= 5.5) {
													if (x[3] <= 2.5) {
														return 14.0f;
													}
													else {
														if (x[3] <= 3.5) {
															return 16.0f;
														}
														else {
															if (x[3] <= 4.5) {
																return 14.0f;
															}
															else {
																return 16.0f;
															}

														}

													}

												}
												else {
													return 14.0f;
												}

											}

										}
										else {
											if (x[3] <= 3.5) {
												if (x[2] <= 4.5) {
													return 11.0f;
												}
												else {
													if (x[3] <= 2.5) {
														if (x[2] <= 5.5) {
															return 14.0f;
														}
														else {
															if (x[2] <= 6.5) {
																return 11.0f;
															}
															else {
																return 14.0f;
															}

														}

													}
													else {
														if (x[2] <= 5.5) {
															return 13.0f;
														}
														else {
															if (x[2] <= 6.5) {
																return 32.0f;
															}
															else {
																return 14.0f;
															}

														}

													}

												}

											}
											else {
												if (x[3] <= 4.5) {
													return 14.0f;
												}
												else {
													if (x[3] <= 5.5) {
														return 11.0f;
													}
													else {
														if (x[2] <= 5.5) {
															return 14.0f;
														}
														else {
															if (x[2] <= 6.5) {
																return 11.0f;
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
									if (x[2] <= 4.5) {
										if (x[3] <= 3.5) {
											if (x[3] <= 2.5) {
												if (x[2] <= 2.5) {
													return 9.0f;
												}
												else {
													if (x[2] <= 3.5) {
														return 14.0f;
													}
													else {
														return 9.0f;
													}

												}

											}
											else {
												return 9.0f;
											}

										}
										else {
											if (x[3] <= 6.5) {
												if (x[2] <= 2.5) {
													if (x[3] <= 4.5) {
														return 17.0f;
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
												if (x[2] <= 2.5) {
													return 37.0f;
												}
												else {
													return 16.0f;
												}

											}

										}

									}
									else {
										if (x[2] <= 5.5) {
											if (x[3] <= 4.5) {
												if (x[3] <= 2.5) {
													return 14.0f;
												}
												else {
													if (x[3] <= 3.5) {
														return 13.0f;
													}
													else {
														return 14.0f;
													}

												}

											}
											else {
												if (x[3] <= 5.5) {
													return 27.0f;
												}
												else {
													if (x[3] <= 6.5) {
														return 14.0f;
													}
													else {
														return 27.0f;
													}

												}

											}

										}
										else {
											if (x[2] <= 6.5) {
												return 14.0f;
											}
											else {
												if (x[3] <= 2.5) {
													return 28.0f;
												}
												else {
													if (x[3] <= 4.5) {
														return 14.0f;
													}
													else {
														if (x[3] <= 6.0) {
															return 28.0f;
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
								if (x[2] <= 3.5) {
									if (x[2] <= 2.5) {
										if (x[3] <= 2.5) {
											return 14.0f;
										}
										else {
											if (x[3] <= 3.5) {
												return 19.0f;
											}
											else {
												if (x[3] <= 4.5) {
													return 14.0f;
												}
												else {
													if (x[3] <= 5.5) {
														return 19.0f;
													}
													else {
														if (x[3] <= 6.5) {
															return 14.0f;
														}
														else {
															return 19.0f;
														}

													}

												}

											}

										}

									}
									else {
										if (x[3] <= 4.5) {
											if (x[3] <= 2.5) {
												return 16.0f;
											}
											else {
												return 19.0f;
											}

										}
										else {
											if (x[3] <= 5.5) {
												return 16.0f;
											}
											else {
												if (x[3] <= 6.5) {
													return 14.0f;
												}
												else {
													return 16.0f;
												}

											}

										}

									}

								}
								else {
									if (x[3] <= 2.5) {
										if (x[2] <= 4.5) {
											return 12.0f;
										}
										else {
											if (x[2] <= 5.5) {
												return 19.0f;
											}
											else {
												if (x[2] <= 6.5) {
													return 38.0f;
												}
												else {
													return 19.0f;
												}

											}

										}

									}
									else {
										if (x[3] <= 4.5) {
											if (x[3] <= 3.5) {
												if (x[2] <= 5.5) {
													return 19.0f;
												}
												else {
													if (x[2] <= 6.5) {
														return 32.0f;
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
											if (x[2] <= 4.5) {
												return 14.0f;
											}
											else {
												if (x[2] <= 5.5) {
													return 19.0f;
												}
												else {
													if (x[2] <= 6.5) {
														return 14.0f;
													}
													else {
														return 19.0f;
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
						if (x[2] <= 2.5) {
							if (x[2] <= 0.5) {
								if (x[3] <= 2.5) {
									return 3.0f;
								}
								else {
									if (x[3] <= 3.5) {
										return 15.0f;
									}
									else {
										if (x[3] <= 4.5) {
											return 3.0f;
										}
										else {
											return 15.0f;
										}

									}

								}

							}
							else {
								if (x[2] <= 1.5) {
									if (x[3] <= 5.5) {
										if (x[3] <= 4.5) {
											if (x[1] <= 1.5) {
												if (x[1] <= 0.5) {
													return 2.0f;
												}
												else {
													if (x[3] <= 2.5) {
														return 2.0f;
													}
													else {
														if (x[3] <= 3.5) {
															return 11.0f;
														}
														else {
															return 2.0f;
														}

													}

												}

											}
											else {
												if (x[3] <= 2.5) {
													if (x[1] <= 2.5) {
														return 2.0f;
													}
													else {
														return 19.0f;
													}

												}
												else {
													if (x[3] <= 3.5) {
														return 15.0f;
													}
													else {
														return 2.0f;
													}

												}

											}

										}
										else {
											return 15.0f;
										}

									}
									else {
										if (x[3] <= 6.5) {
											if (x[1] <= 1.5) {
												return 2.0f;
											}
											else {
												if (x[1] <= 2.5) {
													return 9.0f;
												}
												else {
													return 2.0f;
												}

											}

										}
										else {
											return 2.0f;
										}

									}

								}
								else {
									if (x[3] <= 5.5) {
										if (x[3] <= 4.5) {
											if (x[3] <= 3.5) {
												if (x[3] <= 2.5) {
													if (x[1] <= 2.5) {
														return 17.0f;
													}
													else {
														return 15.0f;
													}

												}
												else {
													if (x[1] <= 1.5) {
														return 15.0f;
													}
													else {
														if (x[1] <= 2.5) {
															return 9.0f;
														}
														else {
															return 15.0f;
														}

													}

												}

											}
											else {
												return 17.0f;
											}

										}
										else {
											return 15.0f;
										}

									}
									else {
										if (x[1] <= 2.5) {
											if (x[3] <= 6.5) {
												if (x[1] <= 1.5) {
													return 11.0f;
												}
												else {
													return 9.0f;
												}

											}
											else {
												return 37.0f;
											}

										}
										else {
											return 19.0f;
										}

									}

								}

							}

						}
						else {
							if (x[1] <= 1.5) {
								if (x[1] <= 0.5) {
									if (x[3] <= 4.5) {
										if (x[2] <= 3.5) {
											if (x[3] <= 2.5) {
												return 18.0f;
											}
											else {
												if (x[3] <= 3.5) {
													return 16.0f;
												}
												else {
													return 18.0f;
												}

											}

										}
										else {
											if (x[3] <= 2.5) {
												if (x[2] <= 4.5) {
													return 12.0f;
												}
												else {
													return 18.0f;
												}

											}
											else {
												if (x[2] <= 4.5) {
													return 18.0f;
												}
												else {
													if (x[3] <= 3.5) {
														return 13.0f;
													}
													else {
														return 18.0f;
													}

												}

											}

										}

									}
									else {
										if (x[3] <= 5.5) {
											return 15.0f;
										}
										else {
											return 18.0f;
										}

									}

								}
								else {
									if (x[2] <= 5.5) {
										if (x[3] <= 4.5) {
											if (x[3] <= 2.5) {
												if (x[2] <= 3.5) {
													return 11.0f;
												}
												else {
													if (x[2] <= 4.5) {
														return 12.0f;
													}
													else {
														return 11.0f;
													}

												}

											}
											else {
												return 11.0f;
											}

										}
										else {
											if (x[3] <= 5.5) {
												return 15.0f;
											}
											else {
												if (x[2] <= 3.5) {
													if (x[3] <= 6.5) {
														return 11.0f;
													}
													else {
														return 16.0f;
													}

												}
												else {
													return 11.0f;
												}

											}

										}

									}
									else {
										if (x[2] <= 6.5) {
											if (x[3] <= 3.5) {
												if (x[3] <= 2.5) {
													return 15.0f;
												}
												else {
													return 32.0f;
												}

											}
											else {
												if (x[3] <= 5.0) {
													return 34.0f;
												}
												else {
													return 36.0f;
												}

											}

										}
										else {
											if (x[3] <= 2.5) {
												return 11.0f;
											}
											else {
												if (x[3] <= 3.5) {
													return 15.0f;
												}
												else {
													if (x[3] <= 4.5) {
														return 11.0f;
													}
													else {
														if (x[3] <= 6.0) {
															return 15.0f;
														}
														else {
															return 11.0f;
														}

													}

												}

											}

										}

									}

								}

							}
							else {
								if (x[1] <= 2.5) {
									if (x[2] <= 4.5) {
										if (x[2] <= 3.5) {
											if (x[3] <= 4.5) {
												return 16.0f;
											}
											else {
												if (x[3] <= 5.5) {
													return 15.0f;
												}
												else {
													if (x[3] <= 6.5) {
														return 9.0f;
													}
													else {
														return 16.0f;
													}

												}

											}

										}
										else {
											if (x[3] <= 2.5) {
												return 12.0f;
											}
											else {
												return 9.0f;
											}

										}

									}
									else {
										if (x[2] <= 5.5) {
											if (x[3] <= 6.5) {
												if (x[3] <= 4.5) {
													return 13.0f;
												}
												else {
													if (x[3] <= 5.5) {
														return 15.0f;
													}
													else {
														return 13.0f;
													}

												}

											}
											else {
												return 27.0f;
											}

										}
										else {
											if (x[2] <= 6.5) {
												if (x[3] <= 2.5) {
													return 38.0f;
												}
												else {
													if (x[3] <= 3.5) {
														return 32.0f;
													}
													else {
														if (x[3] <= 5.0) {
															return 34.0f;
														}
														else {
															return 32.0f;
														}

													}

												}

											}
											else {
												if (x[3] <= 6.0) {
													if (x[3] <= 2.5) {
														return 28.0f;
													}
													else {
														if (x[3] <= 3.5) {
															return 15.0f;
														}
														else {
															if (x[3] <= 4.5) {
																return 28.0f;
															}
															else {
																return 15.0f;
															}

														}

													}

												}
												else {
													return 37.0f;
												}

											}

										}

									}

								}
								else {
									if (x[3] <= 5.5) {
										if (x[2] <= 5.5) {
											if (x[3] <= 4.5) {
												if (x[2] <= 4.5) {
													if (x[3] <= 2.5) {
														return 15.0f;
													}
													else {
														if (x[2] <= 3.5) {
															return 19.0f;
														}
														else {
															if (x[3] <= 3.5) {
																return 15.0f;
															}
															else {
																return 19.0f;
															}

														}

													}

												}
												else {
													return 19.0f;
												}

											}
											else {
												return 15.0f;
											}

										}
										else {
											if (x[2] <= 6.5) {
												if (x[3] <= 2.5) {
													return 15.0f;
												}
												else {
													if (x[3] <= 3.5) {
														return 32.0f;
													}
													else {
														return 34.0f;
													}

												}

											}
											else {
												if (x[3] <= 3.5) {
													return 15.0f;
												}
												else {
													if (x[3] <= 4.5) {
														return 19.0f;
													}
													else {
														return 15.0f;
													}

												}

											}

										}

									}
									else {
										if (x[2] <= 3.5) {
											if (x[3] <= 6.5) {
												return 19.0f;
											}
											else {
												return 16.0f;
											}

										}
										else {
											if (x[2] <= 5.5) {
												return 19.0f;
											}
											else {
												if (x[2] <= 6.5) {
													return 36.0f;
												}
												else {
													return 19.0f;
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
			if (x[1] <= 5.5) {
				if (x[1] <= 4.5) {
					if (x[0] <= 1.5) {
						if (x[0] <= 0.5) {
							if (x[2] <= 2.5) {
								if (x[3] <= 4.5) {
									if (x[2] <= 0.5) {
										if (x[3] <= 0.5) {
											return 8.0f;
										}
										else {
											if (x[3] <= 2.5) {
												return 4.0f;
											}
											else {
												if (x[3] <= 3.5) {
													return 8.0f;
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
									if (x[2] <= 1.5) {
										return 4.0f;
									}
									else {
										if (x[3] <= 5.5) {
											return 4.0f;
										}
										else {
											return 8.0f;
										}

									}

								}

							}
							else {
								if (x[3] <= 3.5) {
									if (x[3] <= 1.5) {
										if (x[2] <= 5.0) {
											if (x[2] <= 3.5) {
												if (x[3] <= 0.5) {
													return 8.0f;
												}
												else {
													return 4.0f;
												}

											}
											else {
												if (x[3] <= 0.5) {
													return 4.0f;
												}
												else {
													return 8.0f;
												}

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
								else {
									if (x[2] <= 3.5) {
										return 4.0f;
									}
									else {
										return 8.0f;
									}

								}

							}

						}
						else {
							if (x[3] <= 0.5) {
								if (x[2] <= 3.5) {
									return 8.0f;
								}
								else {
									return 7.0f;
								}

							}
							else {
								if (x[3] <= 2.5) {
									if (x[2] <= 2.5) {
										if (x[2] <= 1.5) {
											return 7.0f;
										}
										else {
											if (x[3] <= 1.5) {
												return 8.0f;
											}
											else {
												return 7.0f;
											}

										}

									}
									else {
										return 7.0f;
									}

								}
								else {
									if (x[2] <= 3.5) {
										if (x[3] <= 3.5) {
											if (x[2] <= 2.5) {
												return 8.0f;
											}
											else {
												return 7.0f;
											}

										}
										else {
											if (x[3] <= 5.5) {
												return 7.0f;
											}
											else {
												if (x[2] <= 1.5) {
													return 7.0f;
												}
												else {
													if (x[2] <= 2.5) {
														return 8.0f;
													}
													else {
														return 7.0f;
													}

												}

											}

										}

									}
									else {
										if (x[3] <= 3.5) {
											return 7.0f;
										}
										else {
											return 8.0f;
										}

									}

								}

							}

						}

					}
					else {
						if (x[0] <= 2.5) {
							if (x[2] <= 2.5) {
								if (x[3] <= 0.5) {
									return 8.0f;
								}
								else {
									if (x[2] <= 1.5) {
										if (x[3] <= 2.5) {
											return 14.0f;
										}
										else {
											if (x[3] <= 3.5) {
												return 8.0f;
											}
											else {
												if (x[2] <= 0.5) {
													if (x[3] <= 4.5) {
														return 14.0f;
													}
													else {
														return 8.0f;
													}

												}
												else {
													return 14.0f;
												}

											}

										}

									}
									else {
										if (x[3] <= 5.5) {
											if (x[3] <= 3.5) {
												if (x[3] <= 1.5) {
													return 8.0f;
												}
												else {
													if (x[3] <= 2.5) {
														return 14.0f;
													}
													else {
														return 8.0f;
													}

												}

											}
											else {
												return 14.0f;
											}

										}
										else {
											return 8.0f;
										}

									}

								}

							}
							else {
								if (x[3] <= 0.5) {
									if (x[2] <= 3.5) {
										return 8.0f;
									}
									else {
										return 14.0f;
									}

								}
								else {
									if (x[3] <= 3.5) {
										return 14.0f;
									}
									else {
										if (x[3] <= 4.5) {
											if (x[2] <= 3.5) {
												return 14.0f;
											}
											else {
												if (x[2] <= 5.0) {
													return 8.0f;
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

								}

							}

						}
						else {
							if (x[3] <= 2.5) {
								return 8.0f;
							}
							else {
								if (x[3] <= 5.5) {
									if (x[3] <= 4.5) {
										if (x[3] <= 3.5) {
											if (x[2] <= 1.5) {
												return 15.0f;
											}
											else {
												if (x[2] <= 3.5) {
													if (x[2] <= 2.5) {
														return 8.0f;
													}
													else {
														return 15.0f;
													}

												}
												else {
													return 8.0f;
												}

											}

										}
										else {
											return 8.0f;
										}

									}
									else {
										return 15.0f;
									}

								}
								else {
									return 8.0f;
								}

							}

						}

					}

				}
				else {
					if (x[0] <= 2.5) {
						if (x[2] <= 4.5) {
							if (x[0] <= 0.5) {
								if (x[3] <= 2.5) {
									return 10.0f;
								}
								else {
									if (x[3] <= 4.5) {
										if (x[3] <= 3.5) {
											if (x[2] <= 1.5) {
												if (x[2] <= 0.5) {
													return 4.0f;
												}
												else {
													return 10.0f;
												}

											}
											else {
												return 4.0f;
											}

										}
										else {
											if (x[2] <= 3.5) {
												return 10.0f;
											}
											else {
												return 4.0f;
											}

										}

									}
									else {
										return 4.0f;
									}

								}

							}
							else {
								if (x[0] <= 1.5) {
									if (x[3] <= 6.5) {
										if (x[3] <= 2.5) {
											if (x[3] <= 0.5) {
												if (x[2] <= 2.5) {
													return 7.0f;
												}
												else {
													if (x[2] <= 3.5) {
														return 10.0f;
													}
													else {
														return 7.0f;
													}

												}

											}
											else {
												if (x[2] <= 3.5) {
													if (x[2] <= 1.5) {
														if (x[2] <= 0.5) {
															if (x[3] <= 1.5) {
																return 10.0f;
															}
															else {
																return 7.0f;
															}

														}
														else {
															if (x[3] <= 1.5) {
																return 7.0f;
															}
															else {
																return 10.0f;
															}

														}

													}
													else {
														if (x[2] <= 2.5) {
															return 10.0f;
														}
														else {
															if (x[3] <= 1.5) {
																return 7.0f;
															}
															else {
																return 10.0f;
															}

														}

													}

												}
												else {
													return 10.0f;
												}

											}

										}
										else {
											if (x[2] <= 0.5) {
												return 7.0f;
											}
											else {
												if (x[2] <= 3.5) {
													if (x[3] <= 4.5) {
														if (x[3] <= 3.5) {
															if (x[2] <= 1.5) {
																return 10.0f;
															}
															else {
																return 7.0f;
															}

														}
														else {
															if (x[2] <= 1.5) {
																return 7.0f;
															}
															else {
																return 10.0f;
															}

														}

													}
													else {
														if (x[2] <= 2.5) {
															return 7.0f;
														}
														else {
															if (x[3] <= 5.5) {
																return 7.0f;
															}
															else {
																return 10.0f;
															}

														}

													}

												}
												else {
													return 7.0f;
												}

											}

										}

									}
									else {
										if (x[2] <= 1.5) {
											return 10.0f;
										}
										else {
											if (x[2] <= 2.5) {
												return 7.0f;
											}
											else {
												return 10.0f;
											}

										}

									}

								}
								else {
									return 10.0f;
								}

							}

						}
						else {
							if (x[2] <= 5.5) {
								if (x[0] <= 1.5) {
									if (x[0] <= 0.5) {
										if (x[3] <= 1.5) {
											return 22.0f;
										}
										else {
											if (x[3] <= 4.5) {
												if (x[3] <= 2.5) {
													return 4.0f;
												}
												else {
													if (x[3] <= 3.5) {
														return 13.0f;
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
										if (x[3] <= 3.5) {
											if (x[3] <= 0.5) {
												return 22.0f;
											}
											else {
												if (x[3] <= 1.5) {
													return 13.0f;
												}
												else {
													if (x[3] <= 2.5) {
														return 7.0f;
													}
													else {
														return 13.0f;
													}

												}

											}

										}
										else {
											if (x[3] <= 5.5) {
												if (x[3] <= 4.5) {
													return 7.0f;
												}
												else {
													return 22.0f;
												}

											}
											else {
												return 7.0f;
											}

										}

									}

								}
								else {
									return 22.0f;
								}

							}
							else {
								if (x[2] <= 6.5) {
									if (x[3] <= 5.0) {
										return 10.0f;
									}
									else {
										if (x[0] <= 1.5) {
											return 7.0f;
										}
										else {
											return 10.0f;
										}

									}

								}
								else {
									if (x[0] <= 1.5) {
										if (x[3] <= 6.0) {
											if (x[3] <= 3.5) {
												if (x[3] <= 2.5) {
													return 22.0f;
												}
												else {
													return 7.0f;
												}

											}
											else {
												return 22.0f;
											}

										}
										else {
											return 7.0f;
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
						if (x[2] <= 4.5) {
							if (x[3] <= 3.5) {
								if (x[3] <= 2.5) {
									if (x[2] <= 1.5) {
										if (x[2] <= 0.5) {
											if (x[3] <= 1.5) {
												return 15.0f;
											}
											else {
												return 10.0f;
											}

										}
										else {
											if (x[3] <= 1.5) {
												return 10.0f;
											}
											else {
												return 15.0f;
											}

										}

									}
									else {
										if (x[2] <= 2.5) {
											return 15.0f;
										}
										else {
											if (x[3] <= 1.5) {
												if (x[2] <= 3.5) {
													if (x[3] <= 0.5) {
														return 15.0f;
													}
													else {
														return 10.0f;
													}

												}
												else {
													if (x[3] <= 0.5) {
														return 10.0f;
													}
													else {
														return 15.0f;
													}

												}

											}
											else {
												return 15.0f;
											}

										}

									}

								}
								else {
									return 15.0f;
								}

							}
							else {
								if (x[3] <= 4.5) {
									return 10.0f;
								}
								else {
									if (x[3] <= 5.5) {
										return 15.0f;
									}
									else {
										if (x[2] <= 1.5) {
											if (x[3] <= 6.5) {
												return 10.0f;
											}
											else {
												return 15.0f;
											}

										}
										else {
											return 10.0f;
										}

									}

								}

							}

						}
						else {
							if (x[3] <= 2.5) {
								return 15.0f;
							}
							else {
								if (x[3] <= 3.5) {
									if (x[2] <= 5.5) {
										return 13.0f;
									}
									else {
										if (x[2] <= 6.5) {
											return 15.0f;
										}
										else {
											return 22.0f;
										}

									}

								}
								else {
									if (x[2] <= 5.5) {
										if (x[3] <= 5.5) {
											if (x[3] <= 4.5) {
												return 22.0f;
											}
											else {
												return 15.0f;
											}

										}
										else {
											return 22.0f;
										}

									}
									else {
										if (x[2] <= 6.5) {
											return 10.0f;
										}
										else {
											if (x[3] <= 6.0) {
												return 22.0f;
											}
											else {
												return 15.0f;
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
				if (x[1] <= 6.5) {
					if (x[2] <= 2.5) {
						if (x[0] <= 2.5) {
							if (x[0] <= 1.5) {
								if (x[2] <= 1.5) {
									if (x[2] <= 0.5) {
										return 3.0f;
									}
									else {
										if (x[3] <= 4.5) {
											if (x[3] <= 1.5) {
												return 7.0f;
											}
											else {
												if (x[3] <= 2.5) {
													return 2.0f;
												}
												else {
													if (x[3] <= 3.5) {
														return 7.0f;
													}
													else {
														return 2.0f;
													}

												}

											}

										}
										else {
											return 7.0f;
										}

									}

								}
								else {
									if (x[3] <= 2.5) {
										return 17.0f;
									}
									else {
										if (x[3] <= 4.5) {
											if (x[3] <= 3.5) {
												return 7.0f;
											}
											else {
												return 17.0f;
											}

										}
										else {
											return 7.0f;
										}

									}

								}

							}
							else {
								if (x[3] <= 3.5) {
									if (x[2] <= 1.5) {
										return 2.0f;
									}
									else {
										return 17.0f;
									}

								}
								else {
									if (x[3] <= 4.5) {
										return 14.0f;
									}
									else {
										if (x[2] <= 1.5) {
											return 29.0f;
										}
										else {
											if (x[3] <= 5.5) {
												return 33.0f;
											}
											else {
												return 14.0f;
											}

										}

									}

								}

							}

						}
						else {
							if (x[3] <= 3.5) {
								return 15.0f;
							}
							else {
								if (x[2] <= 1.5) {
									if (x[3] <= 4.5) {
										if (x[2] <= 0.5) {
											return 3.0f;
										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[3] <= 5.5) {
											return 15.0f;
										}
										else {
											return 36.0f;
										}

									}

								}
								else {
									if (x[3] <= 4.5) {
										return 17.0f;
									}
									else {
										if (x[3] <= 5.5) {
											return 15.0f;
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
						if (x[3] <= 2.5) {
							if (x[0] <= 2.5) {
								if (x[2] <= 3.5) {
									if (x[3] <= 1.5) {
										return 1.0f;
									}
									else {
										return 29.0f;
									}

								}
								else {
									if (x[2] <= 5.0) {
										return 30.0f;
									}
									else {
										return 29.0f;
									}

								}

							}
							else {
								if (x[2] <= 3.5) {
									return 29.0f;
								}
								else {
									return 15.0f;
								}

							}

						}
						else {
							if (x[0] <= 1.5) {
								if (x[3] <= 5.5) {
									if (x[3] <= 4.5) {
										if (x[2] <= 3.5) {
											if (x[3] <= 3.5) {
												return 29.0f;
											}
											else {
												return 7.0f;
											}

										}
										else {
											if (x[2] <= 5.0) {
												return 7.0f;
											}
											else {
												if (x[3] <= 3.5) {
													return 7.0f;
												}
												else {
													return 29.0f;
												}

											}

										}

									}
									else {
										return 29.0f;
									}

								}
								else {
									if (x[2] <= 5.0) {
										return 7.0f;
									}
									else {
										return 32.0f;
									}

								}

							}
							else {
								if (x[2] <= 3.5) {
									if (x[3] <= 4.5) {
										if (x[3] <= 3.5) {
											return 29.0f;
										}
										else {
											if (x[0] <= 2.5) {
												return 14.0f;
											}
											else {
												return 31.0f;
											}

										}

									}
									else {
										return 29.0f;
									}

								}
								else {
									if (x[2] <= 5.0) {
										if (x[0] <= 2.5) {
											if (x[3] <= 3.5) {
												return 30.0f;
											}
											else {
												return 14.0f;
											}

										}
										else {
											if (x[3] <= 3.5) {
												return 30.0f;
											}
											else {
												if (x[3] <= 5.0) {
													return 34.0f;
												}
												else {
													return 30.0f;
												}

											}

										}

									}
									else {
										if (x[0] <= 2.5) {
											if (x[3] <= 3.5) {
												return 32.0f;
											}
											else {
												return 14.0f;
											}

										}
										else {
											if (x[3] <= 3.5) {
												return 29.0f;
											}
											else {
												return 32.0f;
											}

										}

									}

								}

							}

						}

					}

				}
				else {
					if (x[0] <= 2.5) {
						if (x[0] <= 1.5) {
							if (x[0] <= 0.5) {
								if (x[3] <= 0.5) {
									return 13.0f;
								}
								else {
									if (x[2] <= 6.0) {
										if (x[3] <= 4.5) {
											if (x[3] <= 1.5) {
												return 25.0f;
											}
											else {
												if (x[3] <= 2.5) {
													return 4.0f;
												}
												else {
													if (x[3] <= 3.5) {
														return 25.0f;
													}
													else {
														return 4.0f;
													}

												}

											}

										}
										else {
											if (x[2] <= 4.0) {
												if (x[2] <= 1.5) {
													return 25.0f;
												}
												else {
													if (x[2] <= 2.5) {
														return 4.0f;
													}
													else {
														return 25.0f;
													}

												}

											}
											else {
												return 27.0f;
											}

										}

									}
									else {
										return 28.0f;
									}

								}

							}
							else {
								if (x[2] <= 4.5) {
									if (x[3] <= 2.5) {
										if (x[2] <= 1.5) {
											return 2.0f;
										}
										else {
											if (x[3] <= 1.5) {
												if (x[2] <= 2.5) {
													return 17.0f;
												}
												else {
													if (x[2] <= 3.5) {
														return 1.0f;
													}
													else {
														return 7.0f;
													}

												}

											}
											else {
												return 7.0f;
											}

										}

									}
									else {
										if (x[3] <= 6.5) {
											if (x[3] <= 3.5) {
												if (x[2] <= 2.5) {
													return 7.0f;
												}
												else {
													if (x[2] <= 3.5) {
														return 25.0f;
													}
													else {
														return 7.0f;
													}

												}

											}
											else {
												if (x[2] <= 1.5) {
													if (x[3] <= 4.5) {
														return 2.0f;
													}
													else {
														return 25.0f;
													}

												}
												else {
													if (x[2] <= 3.5) {
														if (x[2] <= 2.5) {
															if (x[3] <= 4.5) {
																return 25.0f;
															}
															else {
																return 7.0f;
															}

														}
														else {
															if (x[3] <= 4.5) {
																return 7.0f;
															}
															else {
																return 25.0f;
															}

														}

													}
													else {
														return 25.0f;
													}

												}

											}

										}
										else {
											return 7.0f;
										}

									}

								}
								else {
									if (x[2] <= 6.0) {
										if (x[3] <= 4.5) {
											return 7.0f;
										}
										else {
											if (x[3] <= 5.5) {
												return 27.0f;
											}
											else {
												return 7.0f;
											}

										}

									}
									else {
										if (x[3] <= 4.5) {
											if (x[3] <= 2.5) {
												return 28.0f;
											}
											else {
												if (x[3] <= 3.5) {
													return 7.0f;
												}
												else {
													return 28.0f;
												}

											}

										}
										else {
											if (x[3] <= 6.0) {
												return 25.0f;
											}
											else {
												return 7.0f;
											}

										}

									}

								}

							}

						}
						else {
							if (x[2] <= 3.5) {
								if (x[3] <= 2.5) {
									if (x[2] <= 2.5) {
										if (x[2] <= 1.5) {
											if (x[3] <= 1.5) {
												return 1.0f;
											}
											else {
												return 25.0f;
											}

										}
										else {
											return 25.0f;
										}

									}
									else {
										if (x[3] <= 1.5) {
											return 1.0f;
										}
										else {
											return 38.0f;
										}

									}

								}
								else {
									if (x[3] <= 3.5) {
										if (x[2] <= 1.5) {
											return 2.0f;
										}
										else {
											return 39.0f;
										}

									}
									else {
										if (x[2] <= 1.5) {
											if (x[3] <= 4.5) {
												return 25.0f;
											}
											else {
												if (x[3] <= 6.0) {
													return 2.0f;
												}
												else {
													return 25.0f;
												}

											}

										}
										else {
											if (x[3] <= 4.5) {
												if (x[2] <= 2.5) {
													return 25.0f;
												}
												else {
													return 31.0f;
												}

											}
											else {
												if (x[3] <= 6.0) {
													return 33.0f;
												}
												else {
													if (x[2] <= 2.5) {
														return 37.0f;
													}
													else {
														return 25.0f;
													}

												}

											}

										}

									}

								}

							}
							else {
								if (x[3] <= 4.5) {
									if (x[2] <= 4.5) {
										if (x[3] <= 1.5) {
											return 12.0f;
										}
										else {
											return 25.0f;
										}

									}
									else {
										return 25.0f;
									}

								}
								else {
									if (x[3] <= 5.5) {
										if (x[2] <= 6.0) {
											return 27.0f;
										}
										else {
											return 28.0f;
										}

									}
									else {
										return 25.0f;
									}

								}

							}

						}

					}
					else {
						if (x[2] <= 4.5) {
							if (x[2] <= 2.5) {
								if (x[2] <= 1.5) {
									if (x[3] <= 3.5) {
										return 15.0f;
									}
									else {
										if (x[3] <= 4.5) {
											return 2.0f;
										}
										else {
											return 15.0f;
										}

									}

								}
								else {
									if (x[3] <= 6.0) {
										if (x[3] <= 1.5) {
											return 17.0f;
										}
										else {
											if (x[3] <= 3.5) {
												return 15.0f;
											}
											else {
												if (x[3] <= 4.5) {
													return 17.0f;
												}
												else {
													return 15.0f;
												}

											}

										}

									}
									else {
										return 37.0f;
									}

								}

							}
							else {
								if (x[3] <= 3.5) {
									if (x[2] <= 3.5) {
										if (x[3] <= 1.5) {
											return 15.0f;
										}
										else {
											if (x[3] <= 2.5) {
												return 38.0f;
											}
											else {
												return 15.0f;
											}

										}

									}
									else {
										return 15.0f;
									}

								}
								else {
									if (x[2] <= 3.5) {
										if (x[3] <= 4.5) {
											return 31.0f;
										}
										else {
											return 15.0f;
										}

									}
									else {
										return 12.0f;
									}

								}

							}

						}
						else {
							if (x[3] <= 3.5) {
								if (x[3] <= 1.5) {
									return 15.0f;
								}
								else {
									if (x[2] <= 6.0) {
										if (x[3] <= 2.5) {
											return 15.0f;
										}
										else {
											return 25.0f;
										}

									}
									else {
										return 25.0f;
									}

								}

							}
							else {
								if (x[2] <= 6.0) {
									if (x[3] <= 6.5) {
										if (x[3] <= 4.5) {
											return 13.0f;
										}
										else {
											if (x[3] <= 5.5) {
												return 15.0f;
											}
											else {
												return 13.0f;
											}

										}

									}
									else {
										return 27.0f;
									}

								}
								else {
									if (x[3] <= 4.5) {
										return 28.0f;
									}
									else {
										if (x[3] <= 6.0) {
											return 15.0f;
										}
										else {
											return 28.0f;
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
		if (x[0] <= 5.5) {
			if (x[0] <= 4.5) {
				if (x[3] <= 3.5) {
					return 5.0f;
				}
				else {
					if (x[3] <= 4.5) {
						if (x[1] <= 3.5) {
							if (x[2] <= 2.5) {
								if (x[2] <= 1.5) {
									return 20.0f;
								}
								else {
									if (x[1] <= 1.5) {
										return 20.0f;
									}
									else {
										if (x[1] <= 2.5) {
											return 9.0f;
										}
										else {
											return 20.0f;
										}

									}

								}

							}
							else {
								return 20.0f;
							}

						}
						else {
							if (x[2] <= 3.5) {
								if (x[1] <= 5.0) {
									if (x[2] <= 1.5) {
										return 20.0f;
									}
									else {
										if (x[2] <= 2.5) {
											return 26.0f;
										}
										else {
											return 20.0f;
										}

									}

								}
								else {
									return 20.0f;
								}

							}
							else {
								if (x[1] <= 5.0) {
									return 20.0f;
								}
								else {
									if (x[2] <= 5.0) {
										return 29.0f;
									}
									else {
										return 20.0f;
									}

								}

							}

						}

					}
					else {
						if (x[3] <= 5.5) {
							return 5.0f;
						}
						else {
							if (x[3] <= 6.5) {
								if (x[2] <= 1.5) {
									if (x[1] <= 2.5) {
										if (x[1] <= 1.5) {
											return 20.0f;
										}
										else {
											return 9.0f;
										}

									}
									else {
										return 20.0f;
									}

								}
								else {
									if (x[1] <= 3.5) {
										return 20.0f;
									}
									else {
										if (x[1] <= 5.0) {
											if (x[2] <= 3.5) {
												return 20.0f;
											}
											else {
												if (x[2] <= 5.0) {
													return 26.0f;
												}
												else {
													return 20.0f;
												}

											}

										}
										else {
											return 20.0f;
										}

									}

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
				if (x[1] <= 4.5) {
					return 6.0f;
				}
				else {
					if (x[1] <= 5.5) {
						if (x[3] <= 2.5) {
							return 21.0f;
						}
						else {
							if (x[3] <= 4.0) {
								if (x[2] <= 2.5) {
									if (x[2] <= 0.5) {
										return 10.0f;
									}
									else {
										if (x[2] <= 1.5) {
											return 21.0f;
										}
										else {
											return 10.0f;
										}

									}

								}
								else {
									return 21.0f;
								}

							}
							else {
								if (x[2] <= 4.0) {
									return 21.0f;
								}
								else {
									if (x[2] <= 6.0) {
										if (x[3] <= 6.0) {
											return 22.0f;
										}
										else {
											return 21.0f;
										}

									}
									else {
										return 21.0f;
									}

								}

							}

						}

					}
					else {
						if (x[1] <= 6.5) {
							return 6.0f;
						}
						else {
							if (x[3] <= 4.0) {
								if (x[2] <= 2.5) {
									if (x[3] <= 1.5) {
										if (x[2] <= 1.5) {
											return 21.0f;
										}
										else {
											return 17.0f;
										}

									}
									else {
										return 21.0f;
									}

								}
								else {
									return 21.0f;
								}

							}
							else {
								if (x[2] <= 6.0) {
									if (x[2] <= 1.5) {
										if (x[3] <= 6.0) {
											return 2.0f;
										}
										else {
											return 21.0f;
										}

									}
									else {
										if (x[2] <= 4.0) {
											return 21.0f;
										}
										else {
											if (x[3] <= 6.0) {
												return 27.0f;
											}
											else {
												return 21.0f;
											}

										}

									}

								}
								else {
									return 28.0f;
								}

							}

						}

					}

				}

			}

		}
		else {
			if (x[0] <= 6.5) {
				if (x[1] <= 3.5) {
					if (x[1] <= 1.5) {
						if (x[1] <= 0.5) {
							if (x[2] <= 2.5) {
								if (x[2] <= 0.5) {
									return 3.0f;
								}
								else {
									return 23.0f;
								}

							}
							else {
								if (x[3] <= 5.0) {
									if (x[3] <= 3.5) {
										return 18.0f;
									}
									else {
										if (x[2] <= 3.5) {
											return 18.0f;
										}
										else {
											if (x[2] <= 4.5) {
												return 12.0f;
											}
											else {
												return 18.0f;
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
							if (x[2] <= 4.5) {
								if (x[2] <= 2.5) {
									if (x[3] <= 5.5) {
										if (x[3] <= 3.5) {
											return 11.0f;
										}
										else {
											if (x[3] <= 4.5) {
												if (x[2] <= 0.5) {
													return 11.0f;
												}
												else {
													return 23.0f;
												}

											}
											else {
												return 11.0f;
											}

										}

									}
									else {
										if (x[2] <= 1.5) {
											return 2.0f;
										}
										else {
											return 11.0f;
										}

									}

								}
								else {
									if (x[2] <= 3.5) {
										if (x[3] <= 2.5) {
											return 11.0f;
										}
										else {
											if (x[3] <= 3.5) {
												return 16.0f;
											}
											else {
												if (x[3] <= 4.5) {
													return 11.0f;
												}
												else {
													if (x[3] <= 5.5) {
														return 16.0f;
													}
													else {
														return 11.0f;
													}

												}

											}

										}

									}
									else {
										if (x[3] <= 3.5) {
											return 11.0f;
										}
										else {
											return 12.0f;
										}

									}

								}

							}
							else {
								if (x[3] <= 4.5) {
									if (x[2] <= 5.5) {
										if (x[3] <= 2.5) {
											return 23.0f;
										}
										else {
											if (x[3] <= 3.5) {
												return 13.0f;
											}
											else {
												return 23.0f;
											}

										}

									}
									else {
										if (x[3] <= 3.5) {
											if (x[3] <= 1.5) {
												return 11.0f;
											}
											else {
												if (x[3] <= 2.5) {
													return 23.0f;
												}
												else {
													return 11.0f;
												}

											}

										}
										else {
											return 23.0f;
										}

									}

								}
								else {
									if (x[2] <= 5.5) {
										if (x[3] <= 5.5) {
											return 11.0f;
										}
										else {
											return 23.0f;
										}

									}
									else {
										return 11.0f;
									}

								}

							}

						}

					}
					else {
						if (x[1] <= 2.5) {
							if (x[2] <= 4.5) {
								if (x[3] <= 5.5) {
									if (x[3] <= 1.5) {
										if (x[2] <= 1.5) {
											return 2.0f;
										}
										else {
											if (x[2] <= 2.5) {
												return 9.0f;
											}
											else {
												if (x[2] <= 3.5) {
													return 1.0f;
												}
												else {
													return 9.0f;
												}

											}

										}

									}
									else {
										if (x[3] <= 3.5) {
											return 9.0f;
										}
										else {
											if (x[2] <= 1.5) {
												return 9.0f;
											}
											else {
												if (x[2] <= 2.5) {
													if (x[3] <= 4.5) {
														return 23.0f;
													}
													else {
														return 9.0f;
													}

												}
												else {
													return 9.0f;
												}

											}

										}

									}

								}
								else {
									if (x[2] <= 2.5) {
										if (x[2] <= 1.5) {
											return 23.0f;
										}
										else {
											return 9.0f;
										}

									}
									else {
										if (x[2] <= 3.5) {
											return 36.0f;
										}
										else {
											return 23.0f;
										}

									}

								}

							}
							else {
								if (x[2] <= 5.5) {
									if (x[3] <= 4.5) {
										return 13.0f;
									}
									else {
										if (x[3] <= 5.5) {
											return 27.0f;
										}
										else {
											return 13.0f;
										}

									}

								}
								else {
									if (x[2] <= 6.5) {
										if (x[3] <= 2.5) {
											if (x[3] <= 1.5) {
												return 9.0f;
											}
											else {
												return 32.0f;
											}

										}
										else {
											return 9.0f;
										}

									}
									else {
										return 28.0f;
									}

								}

							}

						}
						else {
							if (x[2] <= 3.5) {
								if (x[3] <= 1.5) {
									return 1.0f;
								}
								else {
									if (x[2] <= 1.5) {
										if (x[2] <= 0.5) {
											return 3.0f;
										}
										else {
											if (x[3] <= 5.5) {
												if (x[3] <= 3.5) {
													return 2.0f;
												}
												else {
													if (x[3] <= 4.5) {
														return 23.0f;
													}
													else {
														return 2.0f;
													}

												}

											}
											else {
												return 36.0f;
											}

										}

									}
									else {
										if (x[2] <= 2.5) {
											return 23.0f;
										}
										else {
											if (x[3] <= 5.5) {
												if (x[3] <= 2.5) {
													return 23.0f;
												}
												else {
													if (x[3] <= 3.5) {
														return 16.0f;
													}
													else {
														if (x[3] <= 4.5) {
															return 23.0f;
														}
														else {
															return 16.0f;
														}

													}

												}

											}
											else {
												return 36.0f;
											}

										}

									}

								}

							}
							else {
								if (x[2] <= 4.5) {
									if (x[3] <= 2.5) {
										if (x[3] <= 1.5) {
											return 12.0f;
										}
										else {
											return 23.0f;
										}

									}
									else {
										return 12.0f;
									}

								}
								else {
									if (x[3] <= 3.5) {
										if (x[3] <= 2.5) {
											if (x[2] <= 5.5) {
												return 23.0f;
											}
											else {
												if (x[3] <= 1.5) {
													return 32.0f;
												}
												else {
													return 23.0f;
												}

											}

										}
										else {
											if (x[2] <= 5.5) {
												return 13.0f;
											}
											else {
												return 32.0f;
											}

										}

									}
									else {
										if (x[3] <= 5.5) {
											if (x[2] <= 5.5) {
												return 23.0f;
											}
											else {
												if (x[2] <= 6.5) {
													return 34.0f;
												}
												else {
													return 23.0f;
												}

											}

										}
										else {
											if (x[2] <= 5.5) {
												return 23.0f;
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
				else {
					if (x[1] <= 5.0) {
						if (x[2] <= 5.0) {
							if (x[3] <= 3.5) {
								if (x[2] <= 3.5) {
									if (x[3] <= 2.5) {
										return 26.0f;
									}
									else {
										if (x[2] <= 1.5) {
											return 26.0f;
										}
										else {
											if (x[2] <= 2.5) {
												return 17.0f;
											}
											else {
												return 26.0f;
											}

										}

									}

								}
								else {
									if (x[3] <= 1.5) {
										return 30.0f;
									}
									else {
										return 26.0f;
									}

								}

							}
							else {
								if (x[2] <= 1.5) {
									if (x[3] <= 5.5) {
										return 26.0f;
									}
									else {
										return 2.0f;
									}

								}
								else {
									if (x[2] <= 3.5) {
										if (x[3] <= 4.5) {
											if (x[2] <= 2.5) {
												return 23.0f;
											}
											else {
												return 26.0f;
											}

										}
										else {
											return 26.0f;
										}

									}
									else {
										if (x[3] <= 5.0) {
											return 26.0f;
										}
										else {
											return 23.0f;
										}

									}

								}

							}

						}
						else {
							if (x[3] <= 1.5) {
								return 32.0f;
							}
							else {
								if (x[3] <= 5.0) {
									return 26.0f;
								}
								else {
									return 32.0f;
								}

							}

						}

					}
					else {
						if (x[2] <= 2.5) {
							if (x[3] <= 1.5) {
								if (x[2] <= 1.5) {
									return 29.0f;
								}
								else {
									return 17.0f;
								}

							}
							else {
								if (x[3] <= 5.5) {
									if (x[2] <= 1.5) {
										return 23.0f;
									}
									else {
										if (x[3] <= 3.5) {
											if (x[3] <= 2.5) {
												return 23.0f;
											}
											else {
												return 29.0f;
											}

										}
										else {
											return 23.0f;
										}

									}

								}
								else {
									if (x[2] <= 1.5) {
										return 23.0f;
									}
									else {
										return 17.0f;
									}

								}

							}

						}
						else {
							if (x[2] <= 3.5) {
								if (x[3] <= 3.5) {
									return 29.0f;
								}
								else {
									if (x[3] <= 4.5) {
										return 23.0f;
									}
									else {
										return 29.0f;
									}

								}

							}
							else {
								if (x[2] <= 5.0) {
									if (x[3] <= 1.5) {
										return 30.0f;
									}
									else {
										if (x[3] <= 2.5) {
											return 23.0f;
										}
										else {
											if (x[3] <= 3.5) {
												return 30.0f;
											}
											else {
												if (x[3] <= 5.0) {
													return 23.0f;
												}
												else {
													return 30.0f;
												}

											}

										}

									}

								}
								else {
									if (x[3] <= 1.5) {
										return 29.0f;
									}
									else {
										if (x[3] <= 2.5) {
											return 23.0f;
										}
										else {
											if (x[3] <= 3.5) {
												return 29.0f;
											}
											else {
												if (x[3] <= 5.0) {
													return 23.0f;
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

				}

			}
			else {
				if (x[1] <= 3.5) {
					if (x[2] <= 4.5) {
						if (x[1] <= 1.5) {
							if (x[3] <= 6.0) {
								if (x[3] <= 4.0) {
									if (x[2] <= 1.5) {
										if (x[3] <= 2.5) {
											return 24.0f;
										}
										else {
											return 11.0f;
										}

									}
									else {
										if (x[2] <= 2.5) {
											if (x[3] <= 1.5) {
												return 17.0f;
											}
											else {
												return 11.0f;
											}

										}
										else {
											if (x[3] <= 2.5) {
												return 11.0f;
											}
											else {
												if (x[2] <= 3.5) {
													return 24.0f;
												}
												else {
													return 11.0f;
												}

											}

										}

									}

								}
								else {
									if (x[2] <= 1.5) {
										return 11.0f;
									}
									else {
										if (x[2] <= 2.5) {
											return 35.0f;
										}
										else {
											return 11.0f;
										}

									}

								}

							}
							else {
								if (x[2] <= 1.5) {
									return 24.0f;
								}
								else {
									if (x[2] <= 2.5) {
										return 37.0f;
									}
									else {
										return 24.0f;
									}

								}

							}

						}
						else {
							if (x[2] <= 2.5) {
								if (x[2] <= 1.5) {
									if (x[3] <= 1.5) {
										if (x[1] <= 2.5) {
											return 9.0f;
										}
										else {
											return 2.0f;
										}

									}
									else {
										if (x[1] <= 2.5) {
											if (x[3] <= 4.0) {
												if (x[3] <= 2.5) {
													return 24.0f;
												}
												else {
													return 39.0f;
												}

											}
											else {
												return 2.0f;
											}

										}
										else {
											if (x[3] <= 4.0) {
												return 2.0f;
											}
											else {
												return 24.0f;
											}

										}

									}

								}
								else {
									if (x[3] <= 4.0) {
										if (x[1] <= 2.5) {
											if (x[3] <= 1.5) {
												return 17.0f;
											}
											else {
												return 9.0f;
											}

										}
										else {
											return 17.0f;
										}

									}
									else {
										if (x[3] <= 6.0) {
											return 35.0f;
										}
										else {
											return 37.0f;
										}

									}

								}

							}
							else {
								if (x[2] <= 3.5) {
									if (x[1] <= 2.5) {
										if (x[3] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[3] <= 4.0) {
												if (x[3] <= 2.5) {
													return 16.0f;
												}
												else {
													return 39.0f;
												}

											}
											else {
												return 16.0f;
											}

										}

									}
									else {
										if (x[3] <= 2.5) {
											return 16.0f;
										}
										else {
											if (x[3] <= 4.0) {
												return 24.0f;
											}
											else {
												if (x[3] <= 6.0) {
													return 16.0f;
												}
												else {
													return 24.0f;
												}

											}

										}

									}

								}
								else {
									if (x[1] <= 2.5) {
										return 9.0f;
									}
									else {
										return 12.0f;
									}

								}

							}

						}

					}
					else {
						if (x[2] <= 6.0) {
							if (x[3] <= 4.0) {
								if (x[1] <= 2.5) {
									if (x[1] <= 1.5) {
										if (x[3] <= 0.5) {
											return 13.0f;
										}
										else {
											if (x[3] <= 2.5) {
												return 11.0f;
											}
											else {
												return 24.0f;
											}

										}

									}
									else {
										return 13.0f;
									}

								}
								else {
									if (x[3] <= 1.5) {
										return 24.0f;
									}
									else {
										if (x[3] <= 2.5) {
											return 13.0f;
										}
										else {
											return 24.0f;
										}

									}

								}

							}
							else {
								if (x[1] <= 1.5) {
									if (x[3] <= 6.0) {
										return 11.0f;
									}
									else {
										return 24.0f;
									}

								}
								else {
									if (x[1] <= 2.5) {
										return 27.0f;
									}
									else {
										if (x[3] <= 6.0) {
											return 27.0f;
										}
										else {
											return 24.0f;
										}

									}

								}

							}

						}
						else {
							if (x[3] <= 4.0) {
								if (x[1] <= 1.5) {
									return 24.0f;
								}
								else {
									if (x[1] <= 2.5) {
										return 28.0f;
									}
									else {
										return 24.0f;
									}

								}

							}
							else {
								if (x[3] <= 6.0) {
									if (x[1] <= 1.5) {
										return 24.0f;
									}
									else {
										if (x[1] <= 2.5) {
											return 35.0f;
										}
										else {
											return 19.0f;
										}

									}

								}
								else {
									if (x[1] <= 1.5) {
										return 24.0f;
									}
									else {
										if (x[1] <= 2.5) {
											return 37.0f;
										}
										else {
											return 24.0f;
										}

									}

								}

							}

						}

					}

				}
				else {
					if (x[1] <= 4.5) {
						if (x[3] <= 2.5) {
							if (x[2] <= 1.5) {
								return 24.0f;
							}
							else {
								if (x[2] <= 2.5) {
									return 8.0f;
								}
								else {
									if (x[3] <= 1.5) {
										if (x[2] <= 5.0) {
											return 8.0f;
										}
										else {
											return 24.0f;
										}

									}
									else {
										return 24.0f;
									}

								}

							}

						}
						else {
							if (x[3] <= 6.0) {
								return 8.0f;
							}
							else {
								if (x[2] <= 2.5) {
									return 8.0f;
								}
								else {
									return 24.0f;
								}

							}

						}

					}
					else {
						if (x[1] <= 6.0) {
							if (x[2] <= 4.5) {
								if (x[3] <= 2.5) {
									if (x[3] <= 0.5) {
										if (x[2] <= 2.5) {
											if (x[2] <= 0.5) {
												return 10.0f;
											}
											else {
												if (x[2] <= 1.5) {
													return 24.0f;
												}
												else {
													return 10.0f;
												}

											}

										}
										else {
											return 24.0f;
										}

									}
									else {
										return 24.0f;
									}

								}
								else {
									if (x[3] <= 6.0) {
										if (x[3] <= 4.0) {
											if (x[2] <= 2.5) {
												return 24.0f;
											}
											else {
												return 10.0f;
											}

										}
										else {
											return 10.0f;
										}

									}
									else {
										return 24.0f;
									}

								}

							}
							else {
								if (x[2] <= 5.5) {
									if (x[3] <= 1.5) {
										return 24.0f;
									}
									else {
										if (x[3] <= 6.0) {
											return 22.0f;
										}
										else {
											return 24.0f;
										}

									}

								}
								else {
									if (x[3] <= 4.0) {
										return 24.0f;
									}
									else {
										if (x[3] <= 6.0) {
											return 28.0f;
										}
										else {
											return 24.0f;
										}

									}

								}

							}

						}
						else {
							if (x[3] <= 6.0) {
								if (x[3] <= 4.0) {
									if (x[2] <= 6.0) {
										if (x[2] <= 3.5) {
											if (x[2] <= 2.5) {
												if (x[3] <= 1.5) {
													return 24.0f;
												}
												else {
													if (x[2] <= 1.5) {
														if (x[3] <= 2.5) {
															return 24.0f;
														}
														else {
															return 25.0f;
														}

													}
													else {
														return 25.0f;
													}

												}

											}
											else {
												return 24.0f;
											}

										}
										else {
											if (x[3] <= 2.5) {
												return 25.0f;
											}
											else {
												if (x[2] <= 4.5) {
													return 25.0f;
												}
												else {
													return 13.0f;
												}

											}

										}

									}
									else {
										return 24.0f;
									}

								}
								else {
									if (x[2] <= 2.5) {
										if (x[2] <= 1.5) {
											return 25.0f;
										}
										else {
											return 35.0f;
										}

									}
									else {
										if (x[2] <= 4.0) {
											return 25.0f;
										}
										else {
											if (x[2] <= 6.0) {
												return 27.0f;
											}
											else {
												return 25.0f;
											}

										}

									}

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

	}

}