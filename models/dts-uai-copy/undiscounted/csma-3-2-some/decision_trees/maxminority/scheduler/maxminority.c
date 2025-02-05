#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[9] <= 2.5) {
		if (x[12] <= 4.5) {
			if (x[12] <= 0.5) {
				if (x[9] <= 1.5) {
					if (x[0] <= 1.5) {
						if (x[0] <= 0.5) {
							return 0.0f;
						}
						else {
							if (x[4] <= 0.5) {
								return 1.0f;
							}
							else {
								return 7.0f;
							}

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
					if (x[1] <= 0.5) {
						if (x[2] <= 0.5) {
							if (x[4] <= 1.5) {
								if (x[7] <= 2.5) {
									if (x[0] <= 0.5) {
										return 4.0f;
									}
									else {
										return 12.0f;
									}

								}
								else {
									if (x[8] <= 2.5) {
										return 5.0f;
									}
									else {
										return 6.0f;
									}

								}

							}
							else {
								if (x[7] <= 2.5) {
									if (x[0] <= 0.5) {
										return 8.0f;
									}
									else {
										return 12.0f;
									}

								}
								else {
									if (x[7] <= 3.5) {
										if (x[0] <= 0.5) {
											if (x[8] <= 2.5) {
												return 10.0f;
											}
											else {
												return 12.0f;
											}

										}
										else {
											return 12.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[8] <= 2.5) {
												return 10.0f;
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

							}

						}
						else {
							if (x[2] <= 1.5) {
								if (x[4] <= 1.5) {
									if (x[0] <= 0.5) {
										return 6.0f;
									}
									else {
										return 12.0f;
									}

								}
								else {
									if (x[5] <= 1.5) {
										if (x[7] <= 2.5) {
											return 8.0f;
										}
										else {
											return 12.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[7] <= 2.5) {
												return 8.0f;
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

							}
							else {
								if (x[2] <= 2.5) {
									if (x[0] <= 0.5) {
										if (x[7] <= 2.5) {
											return 8.0f;
										}
										else {
											return 12.0f;
										}

									}
									else {
										return 12.0f;
									}

								}
								else {
									if (x[0] <= 0.5) {
										if (x[7] <= 2.5) {
											return 8.0f;
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

						}

					}
					else {
						if (x[1] <= 1.5) {
							if (x[5] <= 1.5) {
								if (x[4] <= 1.5) {
									if (x[8] <= 2.5) {
										return 5.0f;
									}
									else {
										return 6.0f;
									}

								}
								else {
									return 12.0f;
								}

							}
							else {
								if (x[4] <= 1.5) {
									if (x[8] <= 2.5) {
										return 10.0f;
									}
									else {
										return 12.0f;
									}

								}
								else {
									if (x[10] <= 1.0) {
										if (x[0] <= 0.5) {
											if (x[8] <= 2.5) {
												return 10.0f;
											}
											else {
												return 12.0f;
											}

										}
										else {
											return 12.0f;
										}

									}
									else {
										if (x[0] <= 0.5) {
											if (x[8] <= 2.5) {
												return 10.0f;
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

							}

						}
						else {
							if (x[1] <= 2.5) {
								if (x[10] <= 1.0) {
									if (x[0] <= 0.5) {
										if (x[8] <= 2.5) {
											return 10.0f;
										}
										else {
											return 12.0f;
										}

									}
									else {
										return 12.0f;
									}

								}
								else {
									if (x[0] <= 0.5) {
										if (x[8] <= 2.5) {
											return 10.0f;
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
								if (x[10] <= 1.0) {
									if (x[0] <= 0.5) {
										if (x[8] <= 2.5) {
											return 10.0f;
										}
										else {
											return 12.0f;
										}

									}
									else {
										return 12.0f;
									}

								}
								else {
									if (x[0] <= 0.5) {
										if (x[8] <= 2.5) {
											return 10.0f;
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

						}

					}

				}

			}
			else {
				if (x[1] <= 0.5) {
					if (x[12] <= 2.5) {
						if (x[6] <= 1.5) {
							if (x[2] <= 0.5) {
								if (x[5] <= 1.5) {
									if (x[4] <= 1.5) {
										if (x[10] <= 1.5) {
											return 7.0f;
										}
										else {
											return 11.0f;
										}

									}
									else {
										if (x[7] <= 2.5) {
											return 8.0f;
										}
										else {
											return 9.0f;
										}

									}

								}
								else {
									if (x[11] <= 1.5) {
										if (x[8] <= 2.5) {
											return 10.0f;
										}
										else {
											return 7.0f;
										}

									}
									else {
										if (x[7] <= 2.5) {
											return 8.0f;
										}
										else {
											if (x[10] <= 1.0) {
												return 9.0f;
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
									if (x[7] <= 2.5) {
										return 8.0f;
									}
									else {
										if (x[10] <= 1.5) {
											return 7.0f;
										}
										else {
											return 11.0f;
										}

									}

								}
								else {
									if (x[7] <= 2.5) {
										return 8.0f;
									}
									else {
										if (x[10] <= 1.5) {
											return 7.0f;
										}
										else {
											return 11.0f;
										}

									}

								}

							}

						}
						else {
							if (x[2] <= 0.5) {
								if (x[11] <= 0.5) {
									if (x[8] <= 2.5) {
										return 10.0f;
									}
									else {
										if (x[7] <= 2.5) {
											return 8.0f;
										}
										else {
											if (x[10] <= 1.5) {
												return 7.0f;
											}
											else {
												return 11.0f;
											}

										}

									}

								}
								else {
									if (x[10] <= 0.5) {
										if (x[7] <= 2.5) {
											return 8.0f;
										}
										else {
											if (x[11] <= 1.5) {
												return 7.0f;
											}
											else {
												return 9.0f;
											}

										}

									}
									else {
										if (x[10] <= 1.5) {
											return 7.0f;
										}
										else {
											return 11.0f;
										}

									}

								}

							}
							else {
								if (x[2] <= 1.5) {
									if (x[7] <= 2.5) {
										return 8.0f;
									}
									else {
										if (x[10] <= 1.5) {
											return 7.0f;
										}
										else {
											return 11.0f;
										}

									}

								}
								else {
									if (x[7] <= 2.5) {
										return 8.0f;
									}
									else {
										if (x[10] <= 1.5) {
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
					else {
						if (x[2] <= 0.5) {
							if (x[11] <= 1.5) {
								if (x[8] <= 2.5) {
									return 10.0f;
								}
								else {
									if (x[7] <= 2.5) {
										return 8.0f;
									}
									else {
										if (x[10] <= 1.5) {
											return 7.0f;
										}
										else {
											return 11.0f;
										}

									}

								}

							}
							else {
								if (x[6] <= 1.5) {
									if (x[7] <= 2.5) {
										return 8.0f;
									}
									else {
										if (x[10] <= 1.0) {
											return 9.0f;
										}
										else {
											return 11.0f;
										}

									}

								}
								else {
									if (x[7] <= 2.5) {
										return 8.0f;
									}
									else {
										if (x[10] <= 1.0) {
											return 9.0f;
										}
										else {
											return 11.0f;
										}

									}

								}

							}

						}
						else {
							if (x[6] <= 1.5) {
								if (x[7] <= 2.5) {
									return 8.0f;
								}
								else {
									if (x[10] <= 1.5) {
										return 7.0f;
									}
									else {
										return 11.0f;
									}

								}

							}
							else {
								if (x[7] <= 2.5) {
									return 8.0f;
								}
								else {
									if (x[10] <= 1.5) {
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
				else {
					if (x[12] <= 2.5) {
						if (x[6] <= 1.5) {
							if (x[1] <= 1.5) {
								if (x[8] <= 2.5) {
									return 10.0f;
								}
								else {
									if (x[5] <= 1.5) {
										return 9.0f;
									}
									else {
										if (x[10] <= 0.5) {
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
											if (x[2] <= 0.5) {
												if (x[11] <= 1.5) {
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

									}

								}

							}
							else {
								if (x[1] <= 2.5) {
									if (x[8] <= 2.5) {
										return 10.0f;
									}
									else {
										if (x[5] <= 1.5) {
											return 9.0f;
										}
										else {
											if (x[10] <= 0.5) {
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
												if (x[2] <= 0.5) {
													if (x[11] <= 1.5) {
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

										}

									}

								}
								else {
									if (x[2] <= 0.5) {
										if (x[8] <= 2.5) {
											return 10.0f;
										}
										else {
											if (x[11] <= 1.0) {
												return 7.0f;
											}
											else {
												return 9.0f;
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
							if (x[8] <= 2.5) {
								return 10.0f;
							}
							else {
								if (x[1] <= 1.5) {
									if (x[10] <= 0.5) {
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
										if (x[2] <= 0.5) {
											if (x[11] <= 1.5) {
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

								}
								else {
									if (x[1] <= 2.5) {
										if (x[10] <= 0.5) {
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
											if (x[2] <= 0.5) {
												if (x[11] <= 1.5) {
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

									}
									else {
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

								}

							}

						}

					}
					else {
						if (x[6] <= 1.5) {
							if (x[8] <= 2.5) {
								return 10.0f;
							}
							else {
								if (x[10] <= 0.5) {
									if (x[1] <= 1.5) {
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
										if (x[1] <= 2.5) {
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

									}

								}
								else {
									if (x[1] <= 1.5) {
										if (x[2] <= 0.5) {
											if (x[11] <= 1.5) {
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
										if (x[1] <= 2.5) {
											if (x[2] <= 0.5) {
												if (x[11] <= 1.5) {
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
											if (x[2] <= 0.5) {
												if (x[11] <= 1.5) {
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

									}

								}

							}

						}
						else {
							if (x[8] <= 2.5) {
								return 10.0f;
							}
							else {
								if (x[10] <= 0.5) {
									if (x[1] <= 1.5) {
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
										if (x[1] <= 2.5) {
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

									}

								}
								else {
									if (x[1] <= 1.5) {
										if (x[2] <= 0.5) {
											if (x[11] <= 1.5) {
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
										if (x[1] <= 2.5) {
											if (x[2] <= 0.5) {
												if (x[11] <= 1.5) {
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
											if (x[2] <= 0.5) {
												if (x[11] <= 1.5) {
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
				if (x[2] <= 0.5) {
					if (x[11] <= 1.5) {
						if (x[8] <= 2.5) {
							return 10.0f;
						}
						else {
							if (x[10] <= 0.5) {
								if (x[7] <= 2.5) {
									return 8.0f;
								}
								else {
									if (x[12] <= 29.5) {
										return 7.0f;
									}
									else {
										return 16.0f;
									}

								}

							}
							else {
								if (x[10] <= 1.5) {
									return 7.0f;
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

						}

					}
					else {
						if (x[10] <= 1.0) {
							if (x[7] <= 2.5) {
								return 8.0f;
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
								return 11.0f;
							}
							else {
								return 16.0f;
							}

						}

					}

				}
				else {
					if (x[10] <= 1.5) {
						if (x[7] <= 2.5) {
							return 8.0f;
						}
						else {
							if (x[12] <= 29.5) {
								return 7.0f;
							}
							else {
								return 16.0f;
							}

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

			}
			else {
				if (x[6] <= 1.5) {
					if (x[8] <= 2.5) {
						return 10.0f;
					}
					else {
						if (x[12] <= 18.5) {
							if (x[10] <= 0.5) {
								if (x[12] <= 11.0) {
									if (x[1] <= 1.5) {
										if (x[12] <= 7.0) {
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
											if (x[12] <= 9.0) {
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

										}

									}
									else {
										if (x[1] <= 2.5) {
											if (x[12] <= 7.0) {
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
												if (x[12] <= 9.0) {
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

											}

										}
										else {
											if (x[12] <= 7.0) {
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
												if (x[12] <= 9.0) {
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

											}

										}

									}

								}
								else {
									if (x[12] <= 15.0) {
										if (x[12] <= 13.0) {
											if (x[1] <= 1.5) {
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
												if (x[1] <= 2.5) {
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

											}

										}
										else {
											if (x[1] <= 1.5) {
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
												if (x[1] <= 2.5) {
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

											}

										}

									}
									else {
										if (x[12] <= 17.0) {
											if (x[1] <= 1.5) {
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
												if (x[1] <= 2.5) {
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

											}

										}
										else {
											if (x[1] <= 1.5) {
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
												if (x[1] <= 2.5) {
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

											}

										}

									}

								}

							}
							else {
								if (x[12] <= 10.5) {
									if (x[1] <= 1.5) {
										if (x[12] <= 6.5) {
											if (x[2] <= 0.5) {
												if (x[11] <= 1.5) {
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
											if (x[12] <= 8.5) {
												if (x[2] <= 0.5) {
													if (x[11] <= 1.5) {
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
												if (x[2] <= 0.5) {
													if (x[11] <= 1.5) {
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

										}

									}
									else {
										if (x[1] <= 2.5) {
											if (x[12] <= 6.5) {
												if (x[2] <= 0.5) {
													if (x[11] <= 1.5) {
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
												if (x[12] <= 8.5) {
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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

											}

										}
										else {
											if (x[12] <= 6.5) {
												if (x[2] <= 0.5) {
													if (x[11] <= 1.5) {
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
												if (x[12] <= 8.5) {
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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

											}

										}

									}

								}
								else {
									if (x[12] <= 14.5) {
										if (x[12] <= 12.5) {
											if (x[1] <= 1.5) {
												if (x[2] <= 0.5) {
													if (x[11] <= 1.5) {
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
												if (x[1] <= 2.5) {
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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

											}

										}
										else {
											if (x[1] <= 1.5) {
												if (x[2] <= 0.5) {
													if (x[11] <= 1.5) {
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
												if (x[1] <= 2.5) {
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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

											}

										}

									}
									else {
										if (x[12] <= 16.5) {
											if (x[1] <= 1.5) {
												if (x[2] <= 0.5) {
													if (x[11] <= 1.5) {
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
												if (x[1] <= 2.5) {
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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

											}

										}
										else {
											if (x[1] <= 1.5) {
												if (x[2] <= 0.5) {
													if (x[11] <= 1.5) {
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
												if (x[1] <= 2.5) {
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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

											}

										}

									}

								}

							}

						}
						else {
							if (x[12] <= 24.5) {
								if (x[10] <= 0.5) {
									if (x[1] <= 1.5) {
										if (x[12] <= 21.0) {
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
											if (x[12] <= 23.0) {
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

										}

									}
									else {
										if (x[1] <= 2.5) {
											if (x[12] <= 21.0) {
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
												if (x[12] <= 23.0) {
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

											}

										}
										else {
											if (x[12] <= 21.0) {
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
												if (x[12] <= 23.0) {
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

											}

										}

									}

								}
								else {
									if (x[1] <= 1.5) {
										if (x[12] <= 20.5) {
											if (x[2] <= 0.5) {
												if (x[11] <= 1.5) {
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
											if (x[12] <= 22.5) {
												if (x[2] <= 0.5) {
													if (x[11] <= 1.5) {
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
												if (x[2] <= 0.5) {
													if (x[11] <= 1.5) {
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

										}

									}
									else {
										if (x[1] <= 2.5) {
											if (x[12] <= 20.5) {
												if (x[2] <= 0.5) {
													if (x[11] <= 1.5) {
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
												if (x[12] <= 22.5) {
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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

											}

										}
										else {
											if (x[12] <= 20.5) {
												if (x[2] <= 0.5) {
													if (x[11] <= 1.5) {
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
												if (x[12] <= 22.5) {
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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

											}

										}

									}

								}

							}
							else {
								if (x[12] <= 28.5) {
									if (x[10] <= 0.5) {
										if (x[12] <= 27.0) {
											if (x[1] <= 1.5) {
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
												if (x[1] <= 2.5) {
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

											}

										}
										else {
											if (x[1] <= 1.5) {
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
												if (x[1] <= 2.5) {
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

											}

										}

									}
									else {
										if (x[12] <= 26.5) {
											if (x[1] <= 1.5) {
												if (x[2] <= 0.5) {
													if (x[11] <= 1.5) {
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
												if (x[1] <= 2.5) {
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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

											}

										}
										else {
											if (x[1] <= 1.5) {
												if (x[2] <= 0.5) {
													if (x[11] <= 1.5) {
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
												if (x[1] <= 2.5) {
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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
													if (x[2] <= 0.5) {
														if (x[11] <= 1.5) {
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

											}

										}

									}

								}
								else {
									if (x[10] <= 1.5) {
										return 7.0f;
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
					if (x[11] <= 0.5) {
						if (x[8] <= 2.5) {
							return 10.0f;
						}
						else {
							if (x[12] <= 29.5) {
								return 7.0f;
							}
							else {
								return 16.0f;
							}

						}

					}
					else {
						if (x[2] <= 0.5) {
							if (x[11] <= 1.5) {
								return 7.0f;
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
							if (x[12] <= 29.5) {
								return 7.0f;
							}
							else {
								return 16.0f;
							}

						}

					}

				}

			}

		}

	}
	else {
		if (x[7] <= 2.5) {
			if (x[10] <= 10.5) {
				if (x[8] <= 2.5) {
					if (x[7] <= 1.5) {
						if (x[0] <= 1.5) {
							return 10.0f;
						}
						else {
							if (x[3] <= 0.5) {
								if (x[9] <= 3.5) {
									return 2.0f;
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
						return 8.0f;
					}

				}
				else {
					if (x[10] <= 4.5) {
						if (x[2] <= 0.5) {
							if (x[11] <= 1.5) {
								if (x[4] <= 1.5) {
									if (x[6] <= 1.5) {
										if (x[5] <= 1.5) {
											return 7.0f;
										}
										else {
											return 13.0f;
										}

									}
									else {
										if (x[10] <= 2.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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

								}
								else {
									if (x[8] <= 3.5) {
										if (x[10] <= 2.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
										if (x[10] <= 0.5) {
											if (x[3] <= 0.5) {
												if (x[9] <= 3.5) {
													return 2.0f;
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
											if (x[10] <= 2.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}

								}

							}
							else {
								if (x[10] <= 1.0) {
									return 1.0f;
								}
								else {
									return 9.0f;
								}

							}

						}
						else {
							if (x[4] <= 1.5) {
								if (x[11] <= 0.5) {
									if (x[2] <= 1.5) {
										if (x[3] <= 0.5) {
											if (x[12] <= 1.0) {
												return 7.0f;
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
										if (x[2] <= 2.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.0) {
													return 7.0f;
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
											if (x[3] <= 0.5) {
												if (x[12] <= 1.0) {
													return 7.0f;
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

								}
								else {
									if (x[2] <= 1.5) {
										if (x[10] <= 0.5) {
											if (x[3] <= 0.5) {
												return 2.0f;
											}
											else {
												return 7.0f;
											}

										}
										else {
											if (x[10] <= 2.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[2] <= 2.5) {
											if (x[10] <= 0.5) {
												if (x[3] <= 0.5) {
													return 2.0f;
												}
												else {
													return 7.0f;
												}

											}
											else {
												if (x[10] <= 2.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[10] <= 1.5) {
												if (x[3] <= 0.5) {
													return 2.0f;
												}
												else {
													return 7.0f;
												}

											}
											else {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}

								}

							}
							else {
								if (x[2] <= 1.5) {
									if (x[10] <= 0.5) {
										if (x[3] <= 0.5) {
											if (x[9] <= 3.5) {
												return 2.0f;
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
										if (x[10] <= 2.5) {
											if (x[11] <= 0.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
											if (x[11] <= 0.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}

								}
								else {
									if (x[2] <= 2.5) {
										if (x[10] <= 0.5) {
											if (x[3] <= 0.5) {
												if (x[9] <= 3.5) {
													return 2.0f;
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
											if (x[10] <= 2.5) {
												if (x[11] <= 0.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
												if (x[11] <= 0.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}
									else {
										if (x[10] <= 1.0) {
											if (x[3] <= 0.5) {
												if (x[9] <= 3.5) {
													return 2.0f;
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
											if (x[10] <= 2.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 0.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}

							}

						}

					}
					else {
						if (x[2] <= 0.5) {
							if (x[11] <= 1.5) {
								if (x[4] <= 1.5) {
									if (x[10] <= 6.5) {
										if (x[3] <= 0.5) {
											if (x[12] <= 1.5) {
												return 7.0f;
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
										if (x[10] <= 8.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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

								}
								else {
									if (x[8] <= 3.5) {
										if (x[10] <= 6.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[10] <= 8.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[10] <= 6.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[10] <= 8.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}

								}

							}
							else {
								return 9.0f;
							}

						}
						else {
							if (x[4] <= 1.5) {
								if (x[11] <= 0.5) {
									if (x[2] <= 1.5) {
										if (x[10] <= 7.0) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.0) {
													return 7.0f;
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
											if (x[10] <= 9.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}
									else {
										if (x[2] <= 2.5) {
											if (x[10] <= 7.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[10] <= 9.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}
										else {
											if (x[10] <= 7.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[10] <= 9.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}

								}
								else {
									if (x[2] <= 1.5) {
										if (x[10] <= 6.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[10] <= 8.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[2] <= 2.5) {
											if (x[10] <= 6.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[10] <= 8.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[10] <= 6.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[10] <= 8.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}

							}
							else {
								if (x[11] <= 0.5) {
									if (x[2] <= 1.5) {
										if (x[10] <= 7.0) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.0) {
													return 7.0f;
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
											if (x[10] <= 9.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}
									else {
										if (x[2] <= 2.5) {
											if (x[10] <= 7.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[10] <= 9.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}
										else {
											if (x[10] <= 7.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[10] <= 9.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}

								}
								else {
									if (x[2] <= 1.5) {
										if (x[10] <= 6.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[10] <= 8.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[2] <= 2.5) {
											if (x[10] <= 6.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[10] <= 8.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[10] <= 6.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[10] <= 8.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}

							}

						}

					}

				}

			}
			else {
				if (x[11] <= 0.5) {
					if (x[8] <= 2.5) {
						return 10.0f;
					}
					else {
						if (x[10] <= 20.5) {
							if (x[2] <= 1.5) {
								if (x[2] <= 0.5) {
									if (x[10] <= 14.5) {
										if (x[10] <= 12.5) {
											if (x[4] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[8] <= 3.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[4] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[8] <= 3.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}
									else {
										if (x[4] <= 1.5) {
											if (x[10] <= 17.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[10] <= 19.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}
										else {
											if (x[8] <= 3.5) {
												if (x[10] <= 17.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[10] <= 19.0) {
														if (x[3] <= 0.5) {
															if (x[12] <= 1.0) {
																return 7.0f;
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
														if (x[3] <= 0.5) {
															if (x[12] <= 1.0) {
																return 7.0f;
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

											}
											else {
												if (x[10] <= 16.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[10] <= 18.5) {
														if (x[3] <= 0.5) {
															if (x[12] <= 1.5) {
																return 7.0f;
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
														if (x[3] <= 0.5) {
															if (x[12] <= 1.5) {
																return 7.0f;
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

											}

										}

									}

								}
								else {
									if (x[4] <= 1.5) {
										if (x[10] <= 15.0) {
											if (x[10] <= 13.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
											if (x[10] <= 17.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[10] <= 19.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}
									else {
										if (x[10] <= 15.0) {
											if (x[10] <= 13.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
											if (x[10] <= 17.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[10] <= 19.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}

								}

							}
							else {
								if (x[2] <= 2.5) {
									if (x[4] <= 1.5) {
										if (x[10] <= 15.0) {
											if (x[10] <= 13.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
											if (x[10] <= 17.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[10] <= 19.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}
									else {
										if (x[10] <= 15.0) {
											if (x[10] <= 13.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
											if (x[10] <= 17.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[10] <= 19.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}

								}
								else {
									if (x[4] <= 1.5) {
										if (x[10] <= 15.0) {
											if (x[10] <= 13.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
											if (x[10] <= 17.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[10] <= 19.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}
									else {
										if (x[10] <= 15.0) {
											if (x[10] <= 13.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
											if (x[10] <= 17.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[10] <= 19.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}

								}

							}

						}
						else {
							if (x[10] <= 24.5) {
								if (x[10] <= 22.5) {
									if (x[2] <= 1.5) {
										if (x[2] <= 0.5) {
											if (x[4] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[8] <= 3.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[4] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}
									else {
										if (x[2] <= 2.5) {
											if (x[4] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
											if (x[4] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}

								}
								else {
									if (x[2] <= 1.5) {
										if (x[2] <= 0.5) {
											if (x[4] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[8] <= 3.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[4] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}
									else {
										if (x[2] <= 2.5) {
											if (x[4] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
											if (x[4] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}

								}

							}
							else {
								if (x[2] <= 0.5) {
									if (x[10] <= 28.5) {
										if (x[10] <= 26.5) {
											if (x[4] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[8] <= 3.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[4] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[8] <= 3.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}
									else {
										if (x[10] <= 29.5) {
											return 7.0f;
										}
										else {
											return 14.0f;
										}

									}

								}
								else {
									if (x[4] <= 1.5) {
										if (x[10] <= 27.0) {
											if (x[2] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[2] <= 2.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}
										else {
											if (x[2] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[2] <= 2.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}
									else {
										if (x[10] <= 27.0) {
											if (x[2] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[2] <= 2.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}
										else {
											if (x[2] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[2] <= 2.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}

								}

							}

						}

					}

				}
				else {
					if (x[2] <= 0.5) {
						if (x[11] <= 1.5) {
							return 7.0f;
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
						if (x[4] <= 1.5) {
							if (x[10] <= 22.5) {
								if (x[10] <= 16.5) {
									if (x[2] <= 1.5) {
										if (x[10] <= 12.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[10] <= 14.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[2] <= 2.5) {
											if (x[10] <= 12.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[10] <= 14.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[10] <= 12.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[10] <= 14.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}
								else {
									if (x[2] <= 1.5) {
										if (x[10] <= 18.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[10] <= 20.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[2] <= 2.5) {
											if (x[10] <= 18.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[10] <= 20.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[10] <= 18.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[10] <= 20.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}

							}
							else {
								if (x[10] <= 29.5) {
									if (x[2] <= 1.5) {
										if (x[10] <= 24.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[10] <= 26.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[2] <= 2.5) {
											if (x[10] <= 24.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[10] <= 26.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[10] <= 24.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[10] <= 26.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}
								else {
									return 14.0f;
								}

							}

						}
						else {
							if (x[10] <= 24.5) {
								if (x[10] <= 16.5) {
									if (x[2] <= 1.5) {
										if (x[10] <= 12.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[10] <= 14.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[2] <= 2.5) {
											if (x[10] <= 12.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[10] <= 14.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[10] <= 12.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[10] <= 14.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}
								else {
									if (x[10] <= 20.5) {
										if (x[10] <= 18.5) {
											if (x[2] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[2] <= 2.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[2] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[2] <= 2.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}
									else {
										if (x[10] <= 22.5) {
											if (x[2] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[2] <= 2.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[2] <= 1.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[2] <= 2.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}

							}
							else {
								if (x[10] <= 29.5) {
									if (x[10] <= 26.5) {
										if (x[2] <= 1.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[2] <= 2.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[2] <= 1.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[2] <= 2.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
		else {
			if (x[11] <= 8.5) {
				if (x[1] <= 0.5) {
					if (x[10] <= 1.5) {
						if (x[3] <= 0.5) {
							if (x[12] <= 1.5) {
								if (x[7] <= 3.5) {
									if (x[0] <= 0.5) {
										if (x[8] <= 2.5) {
											return 10.0f;
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
									if (x[0] <= 0.5) {
										if (x[2] <= 0.5) {
											if (x[11] <= 1.5) {
												return 7.0f;
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
										return 7.0f;
									}

								}

							}
							else {
								if (x[2] <= 0.5) {
									if (x[0] <= 0.5) {
										if (x[4] <= 1.5) {
											return 17.0f;
										}
										else {
											if (x[8] <= 3.5) {
												return 1.0f;
											}
											else {
												return 2.0f;
											}

										}

									}
									else {
										if (x[11] <= 1.0) {
											return 2.0f;
										}
										else {
											return 13.0f;
										}

									}

								}
								else {
									if (x[4] <= 1.5) {
										return 17.0f;
									}
									else {
										return 2.0f;
									}

								}

							}

						}
						else {
							if (x[2] <= 0.5) {
								if (x[3] <= 1.5) {
									if (x[7] <= 3.5) {
										if (x[6] <= 1.5) {
											if (x[8] <= 2.5) {
												return 10.0f;
											}
											else {
												return 7.0f;
											}

										}
										else {
											if (x[0] <= 0.5) {
												if (x[8] <= 2.5) {
													return 10.0f;
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
										if (x[4] <= 1.5) {
											return 17.0f;
										}
										else {
											if (x[0] <= 0.5) {
												if (x[11] <= 1.5) {
													return 7.0f;
												}
												else {
													return 1.0f;
												}

											}
											else {
												return 7.0f;
											}

										}

									}

								}
								else {
									if (x[3] <= 2.5) {
										if (x[4] <= 1.5) {
											if (x[7] <= 3.5) {
												return 7.0f;
											}
											else {
												return 17.0f;
											}

										}
										else {
											if (x[7] <= 3.5) {
												if (x[0] <= 0.5) {
													if (x[8] <= 2.5) {
														return 10.0f;
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
												if (x[0] <= 0.5) {
													if (x[11] <= 1.5) {
														return 7.0f;
													}
													else {
														return 1.0f;
													}

												}
												else {
													return 7.0f;
												}

											}

										}

									}
									else {
										if (x[4] <= 1.5) {
											if (x[7] <= 3.5) {
												return 7.0f;
											}
											else {
												return 17.0f;
											}

										}
										else {
											if (x[7] <= 3.5) {
												if (x[0] <= 0.5) {
													if (x[8] <= 2.5) {
														return 10.0f;
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
												if (x[0] <= 0.5) {
													if (x[11] <= 1.5) {
														return 7.0f;
													}
													else {
														return 1.0f;
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
							else {
								if (x[2] <= 1.5) {
									if (x[3] <= 1.5) {
										if (x[4] <= 1.5) {
											if (x[7] <= 3.5) {
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
									else {
										if (x[3] <= 2.5) {
											if (x[4] <= 1.5) {
												if (x[7] <= 3.5) {
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
										else {
											if (x[4] <= 1.5) {
												if (x[7] <= 3.5) {
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
									if (x[2] <= 2.5) {
										if (x[3] <= 1.5) {
											if (x[4] <= 1.5) {
												if (x[7] <= 3.5) {
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
										else {
											if (x[3] <= 2.5) {
												if (x[4] <= 1.5) {
													if (x[7] <= 3.5) {
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
											else {
												if (x[4] <= 1.5) {
													if (x[7] <= 3.5) {
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
										if (x[3] <= 1.5) {
											if (x[4] <= 1.5) {
												if (x[7] <= 3.5) {
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
										else {
											if (x[3] <= 2.5) {
												if (x[4] <= 1.5) {
													if (x[7] <= 3.5) {
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
											else {
												if (x[4] <= 1.5) {
													if (x[7] <= 3.5) {
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

								}

							}

						}

					}
					else {
						if (x[0] <= 0.5) {
							if (x[5] <= 1.5) {
								if (x[8] <= 3.5) {
									return 0.0f;
								}
								else {
									return 17.0f;
								}

							}
							else {
								if (x[2] <= 1.5) {
									if (x[2] <= 0.5) {
										if (x[3] <= 0.5) {
											if (x[4] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[6] <= 1.5) {
													if (x[9] <= 3.5) {
														return 0.0f;
													}
													else {
														return 17.0f;
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
										if (x[3] <= 0.5) {
											if (x[4] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[6] <= 1.5) {
													if (x[9] <= 3.5) {
														return 0.0f;
													}
													else {
														return 17.0f;
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
								else {
									if (x[2] <= 2.5) {
										if (x[3] <= 0.5) {
											if (x[4] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[6] <= 1.5) {
													if (x[9] <= 3.5) {
														return 0.0f;
													}
													else {
														return 17.0f;
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
										if (x[3] <= 0.5) {
											if (x[4] <= 1.5) {
												return 0.0f;
											}
											else {
												if (x[6] <= 1.5) {
													if (x[9] <= 3.5) {
														return 0.0f;
													}
													else {
														return 17.0f;
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

						}
						else {
							return 11.0f;
						}

					}

				}
				else {
					if (x[8] <= 2.5) {
						if (x[11] <= 2.5) {
							if (x[0] <= 0.5) {
								return 10.0f;
							}
							else {
								if (x[5] <= 1.5) {
									if (x[10] <= 0.5) {
										if (x[3] <= 0.5) {
											if (x[12] <= 1.0) {
												return 7.0f;
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
										if (x[1] <= 1.5) {
											if (x[4] <= 1.5) {
												if (x[3] <= 0.5) {
													return 2.0f;
												}
												else {
													return 7.0f;
												}

											}
											else {
												if (x[11] <= 0.5) {
													if (x[3] <= 0.5) {
														return 2.0f;
													}
													else {
														return 7.0f;
													}

												}
												else {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[1] <= 2.5) {
												if (x[11] <= 0.5) {
													if (x[3] <= 0.5) {
														return 2.0f;
													}
													else {
														return 7.0f;
													}

												}
												else {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
												if (x[3] <= 0.5) {
													return 2.0f;
												}
												else {
													return 7.0f;
												}

											}

										}

									}

								}
								else {
									if (x[11] <= 0.5) {
										if (x[3] <= 0.5) {
											if (x[9] <= 3.5) {
												return 2.0f;
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
										if (x[1] <= 1.5) {
											if (x[10] <= 0.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
											if (x[1] <= 2.5) {
												if (x[10] <= 0.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}

								}

							}

						}
						else {
							if (x[5] <= 1.5) {
								if (x[10] <= 0.5) {
									if (x[1] <= 1.5) {
										if (x[11] <= 5.0) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.0) {
													return 7.0f;
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
											if (x[11] <= 7.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 5.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 7.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 5.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 7.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}

								}
								else {
									if (x[1] <= 1.5) {
										if (x[11] <= 4.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[11] <= 6.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 4.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 6.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 4.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 6.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}

							}
							else {
								if (x[10] <= 0.5) {
									if (x[1] <= 1.5) {
										if (x[11] <= 5.0) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.0) {
													return 7.0f;
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
											if (x[11] <= 7.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 5.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 7.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 5.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 7.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}

								}
								else {
									if (x[1] <= 1.5) {
										if (x[11] <= 4.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[11] <= 6.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 4.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 6.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 4.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 6.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}

							}

						}

					}
					else {
						if (x[1] <= 1.5) {
							if (x[5] <= 1.5) {
								if (x[10] <= 1.5) {
									return 7.0f;
								}
								else {
									if (x[8] <= 3.5) {
										if (x[2] <= 0.5) {
											return 1.0f;
										}
										else {
											if (x[3] <= 0.5) {
												return 2.0f;
											}
											else {
												return 7.0f;
											}

										}

									}
									else {
										return 17.0f;
									}

								}

							}
							else {
								if (x[2] <= 0.5) {
									if (x[11] <= 1.5) {
										if (x[3] <= 0.5) {
											if (x[12] <= 1.5) {
												return 7.0f;
											}
											else {
												return 2.0f;
											}

										}
										else {
											return 7.0f;
										}

									}
									else {
										if (x[3] <= 0.5) {
											if (x[6] <= 1.5) {
												if (x[9] <= 3.5) {
													return 1.0f;
												}
												else {
													return 17.0f;
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
									if (x[2] <= 1.5) {
										if (x[6] <= 1.5) {
											if (x[9] <= 3.5) {
												if (x[10] <= 1.5) {
													return 7.0f;
												}
												else {
													return 2.0f;
												}

											}
											else {
												return 17.0f;
											}

										}
										else {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
												}
												else {
													return 2.0f;
												}

											}
											else {
												return 7.0f;
											}

										}

									}
									else {
										if (x[2] <= 2.5) {
											if (x[6] <= 1.5) {
												if (x[9] <= 3.5) {
													if (x[10] <= 1.5) {
														return 7.0f;
													}
													else {
														return 2.0f;
													}

												}
												else {
													return 17.0f;
												}

											}
											else {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
													}
													else {
														return 2.0f;
													}

												}
												else {
													return 7.0f;
												}

											}

										}
										else {
											if (x[6] <= 1.5) {
												if (x[9] <= 3.5) {
													if (x[10] <= 1.5) {
														return 7.0f;
													}
													else {
														return 2.0f;
													}

												}
												else {
													return 17.0f;
												}

											}
											else {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
													}
													else {
														return 2.0f;
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
						else {
							if (x[1] <= 2.5) {
								if (x[2] <= 0.5) {
									if (x[11] <= 1.5) {
										if (x[3] <= 0.5) {
											if (x[5] <= 1.5) {
												if (x[8] <= 3.5) {
													return 7.0f;
												}
												else {
													return 17.0f;
												}

											}
											else {
												if (x[12] <= 1.5) {
													return 7.0f;
												}
												else {
													return 2.0f;
												}

											}

										}
										else {
											if (x[3] <= 1.5) {
												if (x[5] <= 1.5) {
													if (x[8] <= 3.5) {
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
											else {
												if (x[3] <= 2.5) {
													if (x[5] <= 1.5) {
														if (x[8] <= 3.5) {
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
												else {
													if (x[5] <= 1.5) {
														if (x[8] <= 3.5) {
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

									}
									else {
										if (x[3] <= 0.5) {
											if (x[5] <= 1.5) {
												return 1.0f;
											}
											else {
												if (x[6] <= 1.5) {
													if (x[9] <= 3.5) {
														return 1.0f;
													}
													else {
														return 17.0f;
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

								}
								else {
									if (x[2] <= 1.5) {
										if (x[6] <= 1.5) {
											if (x[9] <= 3.5) {
												if (x[10] <= 1.5) {
													return 7.0f;
												}
												else {
													return 2.0f;
												}

											}
											else {
												return 17.0f;
											}

										}
										else {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
												}
												else {
													return 2.0f;
												}

											}
											else {
												return 7.0f;
											}

										}

									}
									else {
										if (x[2] <= 2.5) {
											if (x[6] <= 1.5) {
												if (x[9] <= 3.5) {
													if (x[10] <= 1.5) {
														return 7.0f;
													}
													else {
														return 2.0f;
													}

												}
												else {
													return 17.0f;
												}

											}
											else {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
													}
													else {
														return 2.0f;
													}

												}
												else {
													return 7.0f;
												}

											}

										}
										else {
											if (x[6] <= 1.5) {
												if (x[9] <= 3.5) {
													if (x[10] <= 1.5) {
														return 7.0f;
													}
													else {
														return 2.0f;
													}

												}
												else {
													return 17.0f;
												}

											}
											else {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
													}
													else {
														return 2.0f;
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
							else {
								if (x[2] <= 0.5) {
									if (x[11] <= 1.5) {
										if (x[3] <= 0.5) {
											if (x[5] <= 1.5) {
												if (x[8] <= 3.5) {
													return 7.0f;
												}
												else {
													return 17.0f;
												}

											}
											else {
												if (x[12] <= 1.5) {
													return 7.0f;
												}
												else {
													return 2.0f;
												}

											}

										}
										else {
											if (x[3] <= 1.5) {
												if (x[5] <= 1.5) {
													if (x[8] <= 3.5) {
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
											else {
												if (x[3] <= 2.5) {
													if (x[5] <= 1.5) {
														if (x[8] <= 3.5) {
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
												else {
													if (x[5] <= 1.5) {
														if (x[8] <= 3.5) {
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

									}
									else {
										if (x[3] <= 0.5) {
											if (x[5] <= 1.5) {
												return 1.0f;
											}
											else {
												if (x[6] <= 1.5) {
													if (x[9] <= 3.5) {
														return 1.0f;
													}
													else {
														return 17.0f;
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

								}
								else {
									if (x[2] <= 1.5) {
										if (x[6] <= 1.5) {
											if (x[9] <= 3.5) {
												if (x[10] <= 1.5) {
													return 7.0f;
												}
												else {
													return 2.0f;
												}

											}
											else {
												return 17.0f;
											}

										}
										else {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
												}
												else {
													return 2.0f;
												}

											}
											else {
												return 7.0f;
											}

										}

									}
									else {
										if (x[2] <= 2.5) {
											if (x[6] <= 1.5) {
												if (x[9] <= 3.5) {
													if (x[10] <= 1.5) {
														return 7.0f;
													}
													else {
														return 2.0f;
													}

												}
												else {
													return 17.0f;
												}

											}
											else {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
													}
													else {
														return 2.0f;
													}

												}
												else {
													return 7.0f;
												}

											}

										}
										else {
											if (x[6] <= 1.5) {
												if (x[9] <= 3.5) {
													if (x[10] <= 1.5) {
														return 7.0f;
													}
													else {
														return 2.0f;
													}

												}
												else {
													return 17.0f;
												}

											}
											else {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
													}
													else {
														return 2.0f;
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

			}
			else {
				if (x[11] <= 20.5) {
					if (x[1] <= 0.5) {
						if (x[10] <= 1.5) {
							if (x[11] <= 14.5) {
								if (x[5] <= 1.5) {
									if (x[11] <= 10.5) {
										if (x[3] <= 0.5) {
											if (x[12] <= 1.5) {
												return 7.0f;
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
										if (x[11] <= 12.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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

								}
								else {
									if (x[7] <= 3.5) {
										if (x[11] <= 10.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[11] <= 12.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[11] <= 10.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[11] <= 12.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}

								}

							}
							else {
								if (x[5] <= 1.5) {
									if (x[11] <= 16.5) {
										if (x[3] <= 0.5) {
											if (x[12] <= 1.5) {
												return 7.0f;
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
										if (x[11] <= 18.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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

								}
								else {
									if (x[7] <= 3.5) {
										if (x[11] <= 16.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[11] <= 18.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[11] <= 16.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[11] <= 18.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}

								}

							}

						}
						else {
							return 11.0f;
						}

					}
					else {
						if (x[5] <= 1.5) {
							if (x[10] <= 0.5) {
								if (x[11] <= 15.0) {
									if (x[1] <= 1.5) {
										if (x[11] <= 11.0) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.0) {
													return 7.0f;
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
											if (x[11] <= 13.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 11.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 13.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 11.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 13.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}

								}
								else {
									if (x[1] <= 1.5) {
										if (x[11] <= 17.0) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.0) {
													return 7.0f;
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
											if (x[11] <= 19.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 17.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 19.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 17.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 19.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}

								}

							}
							else {
								if (x[11] <= 14.5) {
									if (x[1] <= 1.5) {
										if (x[11] <= 10.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[11] <= 12.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 10.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 12.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 10.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 12.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}
								else {
									if (x[1] <= 1.5) {
										if (x[11] <= 16.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[11] <= 18.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 16.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 18.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 16.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 18.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}

							}

						}
						else {
							if (x[10] <= 0.5) {
								if (x[11] <= 15.0) {
									if (x[1] <= 1.5) {
										if (x[11] <= 11.0) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.0) {
													return 7.0f;
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
											if (x[11] <= 13.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 11.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 13.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 11.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 13.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}

								}
								else {
									if (x[1] <= 1.5) {
										if (x[11] <= 17.0) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.0) {
													return 7.0f;
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
											if (x[11] <= 19.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 17.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 19.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 17.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 19.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}

								}

							}
							else {
								if (x[11] <= 14.5) {
									if (x[1] <= 1.5) {
										if (x[11] <= 10.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[11] <= 12.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 10.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 12.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 10.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 12.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}
								else {
									if (x[1] <= 1.5) {
										if (x[11] <= 16.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[11] <= 18.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 16.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 18.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 16.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 18.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}

							}

						}

					}

				}
				else {
					if (x[11] <= 26.5) {
						if (x[1] <= 0.5) {
							if (x[10] <= 1.5) {
								if (x[5] <= 1.5) {
									if (x[11] <= 22.5) {
										if (x[3] <= 0.5) {
											if (x[12] <= 1.5) {
												return 7.0f;
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
										if (x[11] <= 24.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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

								}
								else {
									if (x[7] <= 3.5) {
										if (x[11] <= 22.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[11] <= 24.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[11] <= 22.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[11] <= 24.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}

								}

							}
							else {
								return 11.0f;
							}

						}
						else {
							if (x[5] <= 1.5) {
								if (x[10] <= 0.5) {
									if (x[1] <= 1.5) {
										if (x[11] <= 23.0) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.0) {
													return 7.0f;
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
											if (x[11] <= 25.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 23.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 25.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 23.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 25.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}

								}
								else {
									if (x[1] <= 1.5) {
										if (x[11] <= 22.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[11] <= 24.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 22.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 24.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 22.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 24.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}

							}
							else {
								if (x[10] <= 0.5) {
									if (x[1] <= 1.5) {
										if (x[11] <= 23.0) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.0) {
													return 7.0f;
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
											if (x[11] <= 25.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 23.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 25.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 23.0) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[11] <= 25.0) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.0) {
															return 7.0f;
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

										}

									}

								}
								else {
									if (x[1] <= 1.5) {
										if (x[11] <= 22.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[11] <= 24.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 2.5) {
											if (x[11] <= 22.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 24.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}
										else {
											if (x[11] <= 22.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[11] <= 24.5) {
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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
													if (x[3] <= 0.5) {
														if (x[12] <= 1.5) {
															return 7.0f;
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

										}

									}

								}

							}

						}

					}
					else {
						if (x[11] <= 29.5) {
							if (x[1] <= 0.5) {
								if (x[10] <= 1.5) {
									if (x[5] <= 1.5) {
										if (x[3] <= 0.5) {
											if (x[12] <= 1.5) {
												return 7.0f;
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
										if (x[7] <= 3.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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

								}
								else {
									return 11.0f;
								}

							}
							else {
								if (x[5] <= 1.5) {
									if (x[10] <= 0.5) {
										if (x[1] <= 1.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.0) {
													return 7.0f;
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
											if (x[1] <= 2.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 1.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[1] <= 2.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}

								}
								else {
									if (x[10] <= 0.5) {
										if (x[1] <= 1.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.0) {
													return 7.0f;
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
											if (x[1] <= 2.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.0) {
														return 7.0f;
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

									}
									else {
										if (x[1] <= 1.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 1.5) {
													return 7.0f;
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
											if (x[1] <= 2.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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
												if (x[3] <= 0.5) {
													if (x[12] <= 1.5) {
														return 7.0f;
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

									}

								}

							}

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