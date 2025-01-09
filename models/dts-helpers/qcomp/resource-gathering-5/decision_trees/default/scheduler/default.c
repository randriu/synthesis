#include <stdio.h>

float classify(const float x[]);

int main() {
    float x[] = {0.f,0.f,0.f,5.f,5.f,3.f,1.f};
    float result = classify(x);
    return 0;
}

float classify(const float x[]) {
	if (x[5] <= 3.5) {
		if (x[2] <= 0.5) {
			if (x[6] <= 4.5) {
				if (x[4] <= 0.5) {
					if (x[1] <= 0.5) {
						return 1.0f;
					}
					else {
						if (x[5] <= 2.5) {
							if (x[6] <= 3.5) {
								return 1.0f;
							}
							else {
								if (x[5] <= 1.5) {
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

				}
				else {
					if (x[1] <= 0.5) {
						if (x[5] <= 2.5) {
							return 0.0f;
						}
						else {
							if (x[3] <= 2.5) {
								return 0.0f;
							}
							else {
								if (x[4] <= 3.5) {
									if (x[6] <= 3.5) {
										if (x[3] <= 3.5) {
											if (x[4] <= 1.5) {
												return 1.0f;
											}
											else {
												return 0.0f;
											}

										}
										else {
											if (x[4] <= 1.5) {
												if (x[3] <= 4.5) {
													return 1.0f;
												}
												else {
													return 0.0f;
												}

											}
											else {
												if (x[3] <= 4.5) {
													if (x[4] <= 2.5) {
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
						if (x[5] <= 2.5) {
							if (x[6] <= 3.5) {
								if (x[5] <= 1.5) {
									return 1.0f;
								}
								else {
									if (x[3] <= 0.5) {
										return 0.0f;
									}
									else {
										if (x[6] <= 1.5) {
											return 1.0f;
										}
										else {
											if (x[3] <= 2.5) {
												if (x[4] <= 1.5) {
													if (x[3] <= 1.5) {
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
												if (x[4] <= 2.5) {
													return 1.0f;
												}
												else {
													if (x[3] <= 3.5) {
														return 0.0f;
													}
													else {
														if (x[4] <= 3.5) {
															return 1.0f;
														}
														else {
															if (x[3] <= 4.5) {
																return 0.0f;
															}
															else {
																if (x[4] <= 4.5) {
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
							else {
								if (x[5] <= 1.5) {
									if (x[3] <= 2.5) {
										if (x[4] <= 1.5) {
											if (x[3] <= 1.5) {
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
										if (x[4] <= 2.5) {
											return 1.0f;
										}
										else {
											if (x[3] <= 3.5) {
												return 0.0f;
											}
											else {
												if (x[4] <= 3.5) {
													return 1.0f;
												}
												else {
													if (x[3] <= 4.5) {
														return 0.0f;
													}
													else {
														if (x[4] <= 4.5) {
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
									if (x[3] <= 2.5) {
										if (x[4] <= 1.5) {
											if (x[3] <= 1.5) {
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
										if (x[4] <= 2.5) {
											return 3.0f;
										}
										else {
											if (x[3] <= 3.5) {
												return 0.0f;
											}
											else {
												if (x[4] <= 3.5) {
													return 3.0f;
												}
												else {
													if (x[3] <= 4.5) {
														return 0.0f;
													}
													else {
														if (x[4] <= 4.5) {
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
							if (x[3] <= 2.5) {
								if (x[4] <= 1.5) {
									if (x[3] <= 1.5) {
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
								if (x[4] <= 2.5) {
									return 3.0f;
								}
								else {
									if (x[3] <= 3.5) {
										return 0.0f;
									}
									else {
										if (x[4] <= 3.5) {
											return 3.0f;
										}
										else {
											if (x[3] <= 4.5) {
												return 0.0f;
											}
											else {
												if (x[4] <= 4.5) {
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
			else {
				if (x[4] <= 0.5) {
					if (x[1] <= 0.5) {
						return 1.0f;
					}
					else {
						if (x[5] <= 1.5) {
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
			if (x[5] <= 1.5) {
				return 1.0f;
			}
			else {
				if (x[1] <= 0.5) {
					if (x[3] <= 1.5) {
						if (x[5] <= 2.5) {
							if (x[6] <= 3.5) {
								return 1.0f;
							}
							else {
								if (x[4] <= 1.5) {
									if (x[3] <= 0.5) {
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
							if (x[4] <= 1.5) {
								if (x[3] <= 0.5) {
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
						if (x[4] <= 2.5) {
							return 1.0f;
						}
						else {
							if (x[3] <= 4.5) {
								if (x[6] <= 1.5) {
									return 1.0f;
								}
								else {
									if (x[4] <= 4.5) {
										if (x[3] <= 3.5) {
											if (x[3] <= 2.5) {
												if (x[4] <= 3.5) {
													if (x[5] <= 2.5) {
														if (x[6] <= 3.5) {
															return 1.0f;
														}
														else {
															return 3.0f;
														}

													}
													else {
														if (x[6] <= 3.5) {
															return 3.0f;
														}
														else {
															return 1.0f;
														}

													}

												}
												else {
													if (x[5] <= 2.5) {
														if (x[6] <= 3.5) {
															return 1.0f;
														}
														else {
															return 3.0f;
														}

													}
													else {
														if (x[6] <= 3.5) {
															return 3.0f;
														}
														else {
															return 1.0f;
														}

													}

												}

											}
											else {
												if (x[4] <= 3.5) {
													return 1.0f;
												}
												else {
													if (x[5] <= 2.5) {
														if (x[6] <= 3.5) {
															return 1.0f;
														}
														else {
															return 3.0f;
														}

													}
													else {
														if (x[6] <= 3.5) {
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
											return 1.0f;
										}

									}
									else {
										if (x[3] <= 3.5) {
											if (x[3] <= 2.5) {
												if (x[5] <= 2.5) {
													if (x[6] <= 3.5) {
														return 1.0f;
													}
													else {
														return 3.0f;
													}

												}
												else {
													if (x[6] <= 3.5) {
														return 3.0f;
													}
													else {
														return 1.0f;
													}

												}

											}
											else {
												if (x[5] <= 2.5) {
													if (x[6] <= 3.5) {
														return 1.0f;
													}
													else {
														return 3.0f;
													}

												}
												else {
													if (x[6] <= 3.5) {
														return 3.0f;
													}
													else {
														return 1.0f;
													}

												}

											}

										}
										else {
											if (x[5] <= 2.5) {
												if (x[6] <= 3.5) {
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
								return 1.0f;
							}

						}

					}

				}
				else {
					if (x[5] <= 2.5) {
						if (x[6] <= 3.5) {
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
		if (x[1] <= 0.5) {
			if (x[5] <= 4.5) {
				if (x[3] <= 0.5) {
					if (x[2] <= 0.5) {
						if (x[6] <= 4.5) {
							return 0.0f;
						}
						else {
							return 2.0f;
						}

					}
					else {
						if (x[6] <= 3.5) {
							return 2.0f;
						}
						else {
							return 3.0f;
						}

					}

				}
				else {
					if (x[6] <= 4.5) {
						if (x[2] <= 0.5) {
							return 1.0f;
						}
						else {
							if (x[4] <= 1.5) {
								return 1.0f;
							}
							else {
								if (x[6] <= 3.5) {
									if (x[3] <= 1.5) {
										return 2.0f;
									}
									else {
										if (x[4] <= 3.5) {
											if (x[3] <= 2.5) {
												if (x[4] <= 2.5) {
													return 1.0f;
												}
												else {
													if (x[6] <= 2.5) {
														return 2.0f;
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
											if (x[3] <= 4.5) {
												if (x[6] <= 2.5) {
													if (x[3] <= 3.5) {
														return 2.0f;
													}
													else {
														if (x[4] <= 4.5) {
															return 1.0f;
														}
														else {
															return 2.0f;
														}

													}

												}
												else {
													if (x[3] <= 3.5) {
														return 1.0f;
													}
													else {
														if (x[4] <= 4.5) {
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

								}
								else {
									return 1.0f;
								}

							}

						}

					}
					else {
						if (x[2] <= 0.5) {
							if (x[4] <= 0.5) {
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

			}
			else {
				if (x[6] <= 4.0) {
					if (x[3] <= 0.5) {
						if (x[2] <= 0.5) {
							if (x[6] <= 2.5) {
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
					else {
						if (x[2] <= 0.5) {
							return 0.0f;
						}
						else {
							if (x[4] <= 1.5) {
								return 0.0f;
							}
							else {
								if (x[6] <= 2.5) {
									if (x[3] <= 1.5) {
										return 2.0f;
									}
									else {
										if (x[3] <= 4.5) {
											if (x[4] <= 2.5) {
												return 0.0f;
											}
											else {
												if (x[3] <= 2.5) {
													if (x[6] <= 1.5) {
														return 2.0f;
													}
													else {
														if (x[4] <= 3.5) {
															return 2.0f;
														}
														else {
															if (x[4] <= 4.5) {
																return 0.0f;
															}
															else {
																return 2.0f;
															}

														}

													}

												}
												else {
													if (x[4] <= 3.5) {
														return 0.0f;
													}
													else {
														if (x[3] <= 3.5) {
															if (x[4] <= 4.5) {
																return 2.0f;
															}
															else {
																if (x[6] <= 1.5) {
																	return 2.0f;
																}
																else {
																	return 0.0f;
																}

															}

														}
														else {
															if (x[4] <= 4.5) {
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
					if (x[3] <= 0.5) {
						if (x[2] <= 0.5) {
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

		}
		else {
			if (x[6] <= 3.5) {
				if (x[3] <= 0.5) {
					if (x[6] <= 1.5) {
						if (x[2] <= 0.5) {
							if (x[5] <= 4.5) {
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
					else {
						return 2.0f;
					}

				}
				else {
					return 2.0f;
				}

			}
			else {
				if (x[2] <= 0.5) {
					if (x[4] <= 0.5) {
						if (x[5] <= 4.5) {
							return 3.0f;
						}
						else {
							if (x[6] <= 4.5) {
								return 2.0f;
							}
							else {
								return 3.0f;
							}

						}

					}
					else {
						if (x[5] <= 4.5) {
							if (x[6] <= 4.5) {
								if (x[3] <= 2.5) {
									if (x[4] <= 1.5) {
										if (x[3] <= 1.5) {
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
								else {
									if (x[4] <= 2.5) {
										return 3.0f;
									}
									else {
										if (x[3] <= 3.5) {
											return 2.0f;
										}
										else {
											if (x[4] <= 3.5) {
												return 3.0f;
											}
											else {
												if (x[3] <= 4.5) {
													return 2.0f;
												}
												else {
													if (x[4] <= 4.5) {
														return 3.0f;
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
								return 2.0f;
							}

						}
						else {
							return 2.0f;
						}

					}

				}
				else {
					if (x[5] <= 4.5) {
						return 3.0f;
					}
					else {
						if (x[6] <= 4.5) {
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

}