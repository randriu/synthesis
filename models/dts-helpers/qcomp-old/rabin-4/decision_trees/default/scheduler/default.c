#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,0.f,1.f,0.f,0.f,0.f,0.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[6] <= 0.5) {
		if (x[7] <= 0.5) {
			if (x[8] <= 0.5) {
				if (x[9] <= 0.5) {
					if (x[1] <= 0.5) {
						if (x[3] <= 0.5) {
							if (x[12] <= 0.5) {
								if (x[2] <= 0.5) {
									if (x[0] <= 0.5) {
										if (x[13] <= 0.5) {
											return 0.0f;
										}
										else {
											return 1.0f;
										}

									}
									else {
										return 9.0f;
									}

								}
								else {
									if (x[4] <= 2.5) {
										if (x[2] <= 1.5) {
											if (x[0] <= 1.5) {
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
										if (x[2] <= 3.5) {
											if (x[0] <= 3.5) {
												if (x[2] <= 2.5) {
													return 9.0f;
												}
												else {
													return 7.0f;
												}

											}
											else {
												return 9.0f;
											}

										}
										else {
											if (x[4] <= 4.5) {
												return 7.0f;
											}
											else {
												if (x[2] <= 4.5) {
													return 9.0f;
												}
												else {
													if (x[2] <= 5.5) {
														if (x[0] <= 5.5) {
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
								if (x[2] <= 0.5) {
									if (x[0] <= 0.5) {
										if (x[13] <= 0.5) {
											return 0.0f;
										}
										else {
											return 1.0f;
										}

									}
									else {
										return 10.0f;
									}

								}
								else {
									if (x[4] <= 2.5) {
										if (x[2] <= 1.5) {
											if (x[0] <= 1.5) {
												return 7.0f;
											}
											else {
												return 10.0f;
											}

										}
										else {
											return 7.0f;
										}

									}
									else {
										if (x[2] <= 3.5) {
											if (x[0] <= 3.5) {
												if (x[2] <= 2.5) {
													return 10.0f;
												}
												else {
													return 7.0f;
												}

											}
											else {
												return 10.0f;
											}

										}
										else {
											if (x[4] <= 4.5) {
												return 7.0f;
											}
											else {
												if (x[2] <= 4.5) {
													return 10.0f;
												}
												else {
													if (x[2] <= 5.5) {
														if (x[0] <= 5.5) {
															return 7.0f;
														}
														else {
															return 10.0f;
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
							if (x[4] <= 0.5) {
								if (x[2] <= 2.5) {
									if (x[0] <= 2.5) {
										if (x[2] <= 0.5) {
											return 8.0f;
										}
										else {
											if (x[2] <= 1.5) {
												if (x[0] <= 1.5) {
													return 7.0f;
												}
												else {
													return 8.0f;
												}

											}
											else {
												return 7.0f;
											}

										}

									}
									else {
										return 8.0f;
									}

								}
								else {
									if (x[3] <= 3.5) {
										return 7.0f;
									}
									else {
										if (x[2] <= 4.5) {
											if (x[0] <= 4.5) {
												if (x[2] <= 3.5) {
													return 8.0f;
												}
												else {
													return 7.0f;
												}

											}
											else {
												return 8.0f;
											}

										}
										else {
											if (x[3] <= 5.5) {
												return 7.0f;
											}
											else {
												if (x[2] <= 5.5) {
													return 8.0f;
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
									if (x[11] <= 0.5) {
										return 11.0f;
									}
									else {
										return 12.0f;
									}

								}
								else {
									if (x[10] <= 0.5) {
										return 13.0f;
									}
									else {
										return 14.0f;
									}

								}

							}

						}

					}
					else {
						if (x[2] <= 0.5) {
							if (x[3] <= 0.5) {
								if (x[12] <= 0.5) {
									if (x[4] <= 2.5) {
										if (x[1] <= 1.5) {
											if (x[0] <= 1.5) {
												return 6.0f;
											}
											else {
												return 9.0f;
											}

										}
										else {
											return 6.0f;
										}

									}
									else {
										if (x[1] <= 3.5) {
											if (x[0] <= 3.5) {
												if (x[1] <= 2.5) {
													return 9.0f;
												}
												else {
													return 6.0f;
												}

											}
											else {
												return 9.0f;
											}

										}
										else {
											if (x[4] <= 4.5) {
												return 6.0f;
											}
											else {
												if (x[1] <= 4.5) {
													return 9.0f;
												}
												else {
													if (x[1] <= 5.5) {
														if (x[0] <= 5.5) {
															return 6.0f;
														}
														else {
															return 9.0f;
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
								else {
									if (x[4] <= 2.5) {
										if (x[1] <= 1.5) {
											if (x[0] <= 1.5) {
												return 6.0f;
											}
											else {
												return 10.0f;
											}

										}
										else {
											return 6.0f;
										}

									}
									else {
										if (x[1] <= 3.5) {
											if (x[0] <= 3.5) {
												if (x[1] <= 2.5) {
													return 10.0f;
												}
												else {
													return 6.0f;
												}

											}
											else {
												return 10.0f;
											}

										}
										else {
											if (x[4] <= 4.5) {
												return 6.0f;
											}
											else {
												if (x[1] <= 4.5) {
													return 10.0f;
												}
												else {
													if (x[1] <= 5.5) {
														if (x[0] <= 5.5) {
															return 6.0f;
														}
														else {
															return 10.0f;
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
							else {
								if (x[11] <= 0.5) {
									if (x[4] <= 0.5) {
										if (x[1] <= 3.5) {
											if (x[0] <= 3.5) {
												if (x[1] <= 2.5) {
													if (x[0] <= 2.5) {
														if (x[1] <= 1.5) {
															if (x[0] <= 1.5) {
																return 6.0f;
															}
															else {
																return 8.0f;
															}

														}
														else {
															return 6.0f;
														}

													}
													else {
														return 8.0f;
													}

												}
												else {
													return 6.0f;
												}

											}
											else {
												return 8.0f;
											}

										}
										else {
											if (x[3] <= 4.5) {
												return 6.0f;
											}
											else {
												if (x[1] <= 4.5) {
													return 8.0f;
												}
												else {
													if (x[1] <= 5.5) {
														if (x[0] <= 5.5) {
															return 6.0f;
														}
														else {
															return 8.0f;
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
										if (x[1] <= 4.5) {
											if (x[0] <= 4.5) {
												if (x[1] <= 3.5) {
													if (x[0] <= 3.5) {
														if (x[1] <= 2.5) {
															if (x[0] <= 2.5) {
																if (x[1] <= 1.5) {
																	if (x[0] <= 1.5) {
																		return 6.0f;
																	}
																	else {
																		return 11.0f;
																	}

																}
																else {
																	return 6.0f;
																}

															}
															else {
																return 11.0f;
															}

														}
														else {
															return 6.0f;
														}

													}
													else {
														return 11.0f;
													}

												}
												else {
													return 6.0f;
												}

											}
											else {
												return 11.0f;
											}

										}
										else {
											if (x[1] <= 5.5) {
												if (x[0] <= 5.5) {
													return 6.0f;
												}
												else {
													return 11.0f;
												}

											}
											else {
												return 6.0f;
											}

										}

									}

								}
								else {
									if (x[4] <= 0.5) {
										if (x[1] <= 3.5) {
											if (x[0] <= 3.5) {
												if (x[1] <= 2.5) {
													if (x[0] <= 2.5) {
														if (x[1] <= 1.5) {
															if (x[0] <= 1.5) {
																return 6.0f;
															}
															else {
																return 8.0f;
															}

														}
														else {
															return 6.0f;
														}

													}
													else {
														return 8.0f;
													}

												}
												else {
													return 6.0f;
												}

											}
											else {
												return 8.0f;
											}

										}
										else {
											if (x[3] <= 4.5) {
												return 6.0f;
											}
											else {
												if (x[1] <= 4.5) {
													return 8.0f;
												}
												else {
													if (x[1] <= 5.5) {
														if (x[0] <= 5.5) {
															return 6.0f;
														}
														else {
															return 8.0f;
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
										if (x[1] <= 4.5) {
											if (x[0] <= 4.5) {
												if (x[1] <= 3.5) {
													if (x[0] <= 3.5) {
														if (x[1] <= 2.5) {
															if (x[0] <= 2.5) {
																if (x[1] <= 1.5) {
																	if (x[0] <= 1.5) {
																		return 6.0f;
																	}
																	else {
																		return 12.0f;
																	}

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
															return 6.0f;
														}

													}
													else {
														return 12.0f;
													}

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
											if (x[1] <= 5.5) {
												if (x[0] <= 5.5) {
													return 6.0f;
												}
												else {
													return 12.0f;
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
						else {
							if (x[1] <= 4.5) {
								if (x[2] <= 4.5) {
									if (x[0] <= 4.5) {
										if (x[1] <= 3.5) {
											if (x[2] <= 3.5) {
												if (x[0] <= 3.5) {
													if (x[1] <= 2.5) {
														if (x[2] <= 2.5) {
															if (x[0] <= 2.5) {
																if (x[1] <= 1.5) {
																	if (x[2] <= 1.5) {
																		if (x[0] <= 1.5) {
																			return 6.0f;
																		}
																		else {
																			if (x[3] <= 1.5) {
																				if (x[3] <= 0.5) {
																					if (x[12] <= 0.5) {
																						return 9.0f;
																					}
																					else {
																						return 10.0f;
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
																	else {
																		return 7.0f;
																	}

																}
																else {
																	return 6.0f;
																}

															}
															else {
																if (x[3] <= 2.5) {
																	if (x[3] <= 0.5) {
																		if (x[12] <= 0.5) {
																			return 9.0f;
																		}
																		else {
																			return 10.0f;
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
														else {
															return 7.0f;
														}

													}
													else {
														return 6.0f;
													}

												}
												else {
													if (x[3] <= 3.5) {
														if (x[3] <= 0.5) {
															if (x[12] <= 0.5) {
																return 9.0f;
															}
															else {
																return 10.0f;
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
											else {
												return 7.0f;
											}

										}
										else {
											return 6.0f;
										}

									}
									else {
										if (x[3] <= 4.5) {
											if (x[3] <= 0.5) {
												if (x[12] <= 0.5) {
													return 9.0f;
												}
												else {
													return 10.0f;
												}

											}
											else {
												return 15.0f;
											}

										}
										else {
											if (x[4] <= 5.5) {
												return 8.0f;
											}
											else {
												if (x[3] <= 5.5) {
													return 15.0f;
												}
												else {
													return 8.0f;
												}

											}

										}

									}

								}
								else {
									if (x[3] <= 5.5) {
										if (x[4] <= 5.5) {
											return 7.0f;
										}
										else {
											if (x[2] <= 5.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 0.5) {
														return 9.0f;
													}
													else {
														return 10.0f;
													}

												}
												else {
													return 15.0f;
												}

											}
											else {
												return 7.0f;
											}

										}

									}
									else {
										if (x[2] <= 5.5) {
											return 8.0f;
										}
										else {
											return 7.0f;
										}

									}

								}

							}
							else {
								if (x[2] <= 5.5) {
									if (x[3] <= 5.5) {
										if (x[4] <= 5.5) {
											return 6.0f;
										}
										else {
											if (x[1] <= 5.5) {
												if (x[3] <= 0.5) {
													if (x[12] <= 0.5) {
														return 9.0f;
													}
													else {
														return 10.0f;
													}

												}
												else {
													return 15.0f;
												}

											}
											else {
												return 6.0f;
											}

										}

									}
									else {
										if (x[1] <= 5.5) {
											return 8.0f;
										}
										else {
											return 6.0f;
										}

									}

								}
								else {
									if (x[1] <= 5.5) {
										return 7.0f;
									}
									else {
										return 6.0f;
									}

								}

							}

						}

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
			return 3.0f;
		}

	}
	else {
		return 2.0f;
	}

}